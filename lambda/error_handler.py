"""
AWS Lambda function to handle errors and publish notifications to SNS.
"""

import os
import json
import logging
import boto3
from typing import Dict
from datetime import datetime

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))

sns_client = boto3.client('sns')


def lambda_handler(event: Dict, context) -> Dict:
    """
    Handle error and publish formatted notification to SNS.

    Expected event structure (from Step Functions error):
    {
        "error": "...",
        "cause": "...",
        "config": {...},
        "provider": "aws",
        ...
    }
    """
    try:
        sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')

        if not sns_topic_arn:
            raise ValueError(
                "Missing required environment variable: SNS_TOPIC_ARN")

        # Extract error information
        error_type = event.get('error', 'UnknownError')
        error_cause = event.get('cause', 'No cause provided')

        # Try to parse cause if it's JSON
        try:
            cause_data = json.loads(error_cause)
            if isinstance(cause_data, dict):
                error_message = cause_data.get('errorMessage', error_cause)
            else:
                error_message = str(cause_data)
        except (json.JSONDecodeError, AttributeError):
            error_message = error_cause

        # Extract context
        provider = event.get('provider', 'Unknown')
        namespace = event.get('namespace', 'Unknown')
        version = event.get('version') or event.get(
            'resolvedVersion', 'Unknown')
        bucket = event.get('bucket', 'Unknown')
        key = event.get('key', 'Unknown')

        logger.info(f"Handling error for {namespace}/{provider} v{version}")
        logger.info(f"Error type: {error_type}")

        # Format email subject
        subject = f"❌ Terraform Provider Sync Failed: {namespace}/{provider}"

        # Format email body
        body = format_error_email(
            error_type=error_type,
            error_message=error_message,
            provider=provider,
            namespace=namespace,
            version=version,
            bucket=bucket,
            key=key,
            event=event
        )

        # Publish to SNS
        logger.info(f"Publishing error notification to SNS: {sns_topic_arn}")
        response = sns_client.publish(
            TopicArn=sns_topic_arn,
            Subject=subject,
            Message=body
        )
        logger.info(
            f"SNS notification sent, MessageId: {response['MessageId']}")

        return {
            'statusCode': 200,
            'notificationSent': True,
            'messageId': response['MessageId']
        }

    except Exception as e:
        logger.error(f"Error publishing to SNS: {str(e)}")
        # Don't raise - we don't want error notification failures to fail the
        # workflow
        return {
            'statusCode': 500,
            'notificationSent': False,
            'error': str(e)
        }


def format_error_email(error_type: str, error_message: str, provider: str,
                       namespace: str, version: str, bucket: str, key: str,
                       event: Dict) -> str:
    """Format error as readable email."""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

    email_body = f"""
Terraform Provider Synchronization Failed
==========================================

TIMESTAMP: {timestamp}

PROVIDER DETAILS
----------------
Provider:   {namespace}/{provider}
Version:    {version}
Config:     s3://{bucket}/{key}

ERROR INFORMATION
-----------------
Error Type: {error_type}

Error Message:
{error_message}

WORKFLOW CONTEXT
----------------
"""

    # Add relevant context fields
    if event.get('versionExists') is not None:
        email_body += f"Version Exists on HCP: {event['versionExists']}\n"

    if event.get('resolvedVersion'):
        email_body += f"Resolved Version: {event['resolvedVersion']}\n"

    if event.get('shouldProcess') is not None:
        email_body += f"Should Process: {event['shouldProcess']}\n"

    # Add platforms if available
    platforms = event.get('platforms', [])
    if platforms:
        email_body += f"\nPlatforms ({len(platforms)}):\n"
        for platform in platforms:
            email_body += f"  - {platform.get('os', 'unknown')}/{platform.get('arch', 'unknown')}\n"

    # Add footer
    email_body += """
TROUBLESHOOTING
---------------
1. Check the config file in S3 is valid JSON
2. Verify TFC_TOKEN and TFC_ORGANIZATION are set correctly
3. Ensure GPG key exists on HCP Terraform
4. Check provider version exists in public registry
5. Review CloudWatch Logs for detailed error traces

NEXT STEPS
----------
- Review the error message above
- Check the Step Functions execution in AWS Console
- Verify the configuration file
- Re-run the workflow after fixing the issue

---
This notification was generated automatically by the Terraform Provider Synchronization workflow.
"""

    return email_body
