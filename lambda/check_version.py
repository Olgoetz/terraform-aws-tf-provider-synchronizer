"""
AWS Lambda function to check if provider version exists on HCP Terraform.
"""

import os
import logging
import boto3
import requests
import tempfile
from typing import Dict, Optional

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))

# Secrets Manager client
secretsmanager = boto3.client('secretsmanager')

# Global CA bundle path
_ca_bundle_path: Optional[str] = None


def get_ca_bundle_path() -> Optional[str]:
    """Get CA bundle path from Secrets Manager."""
    global _ca_bundle_path

    if _ca_bundle_path:
        return _ca_bundle_path

    ca_secret_name = os.environ.get('CA_BUNDLE_SECRET_NAME')
    if not ca_secret_name:
        logger.debug("No CA bundle secret configured")
        return None

    try:
        logger.info(f"Retrieving CA bundle from Secrets Manager: {ca_secret_name}")
        ca_bundle = get_secret(ca_secret_name)

        # Write to temp file
        fd, path = tempfile.mkstemp(suffix='.pem')
        with os.fdopen(fd, 'w') as f:
            f.write(ca_bundle)

        _ca_bundle_path = path
        logger.info(f"CA bundle written to: {path}")
        return path
    except Exception as e:
        logger.warning(f"Failed to retrieve CA bundle: {e}. Using default CA verification.")
        return None


def get_secret(secret_name: str) -> str:
    """Retrieve secret from AWS Secrets Manager."""
    try:
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except Exception as e:
        logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
        raise


def lambda_handler(event: Dict, context) -> Dict:
    """
    Check if provider version already exists on HCP Terraform.
    Version resolution ("latest" → actual version) is done by read_config Lambda.

    Expected event structure:
    {
        "config": {...},
        "provider": "aws",
        "namespace": "hashicorp",
        "version": "6.26.0",  # Already resolved, never "latest"
        ...
    }

    Returns:
    {
        "versionExists": true/false,
        "shouldProcess": true/false,
        ...original event fields
    }
    """
    try:
        # Get configuration from environment
        secret_name = os.environ.get('TFC_TOKEN_SECRET_NAME')
        organization = os.environ.get('TFC_ORGANIZATION')
        tfc_address = os.environ.get('TFC_ADDRESS', 'https://app.terraform.io')

        if not secret_name or not organization:
            raise ValueError(
                "Missing required environment variables: TFC_TOKEN_SECRET_NAME, TFC_ORGANIZATION")

        # Retrieve token from Secrets Manager
        logger.debug(
            f"Retrieving TFC token from Secrets Manager: {secret_name}")
        token = get_secret(secret_name)

        provider = event['provider']
        namespace = event['namespace']
        version = event['version']  # Already resolved by read_config Lambda

        logger.info(f"Checking if {namespace}/{provider} v{version} exists on {tfc_address}")

        # Check if version exists on HCP/TFE
        version_exists = check_version_on_hcp(
            organization, provider, version, token, tfc_address
        )
        logger.info(
            f"Version exists: {version_exists}, should process: {not version_exists}")

        # Add results to event
        return {
            **event,
            'versionExists': version_exists,
            'shouldProcess': not version_exists,
            'statusCode': 200
        }

    except Exception as e:
        logger.error(f"Error checking HCP version: {str(e)}")
        raise Exception(f"Error checking HCP version: {str(e)}")


def check_version_on_hcp(
        organization: str,
        provider: str,
        version: str,
        token: str,
        tfc_address: str = 'https://app.terraform.io') -> bool:
    """Check if version exists on HCP Terraform or Terraform Enterprise."""
    url = (
        f"{tfc_address}/api/v2/organizations/{organization}/"
        f"registry-providers/private/{organization}/{provider}/versions/{version}")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.api+json"
    }

    ca_bundle = get_ca_bundle_path()
    verify = ca_bundle if ca_bundle else True

    logger.info(f"Checking version existence at: {url}")
    logger.debug(f"Using CA bundle: {ca_bundle}")

    # Explicitly disable proxy for VPC-to-TFE communication
    response = requests.get(url, headers=headers, timeout=10, verify=verify, proxies={})

    logger.info(f"Response status: {response.status_code}")
    if response.status_code not in [200, 404]:
        logger.warning(f"Unexpected status code: {response.status_code}, Response: {response.text}")

    return response.status_code == 200
