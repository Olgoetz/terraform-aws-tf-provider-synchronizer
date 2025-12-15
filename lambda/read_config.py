"""
AWS Lambda function to read provider configuration from S3.
"""

import json
import os
import logging
import boto3
import requests
from typing import Dict

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))

s3_client = boto3.client('s3')


def lambda_handler(event: Dict, context) -> Dict:
    """
    Read provider configuration from S3 bucket.
    Supports both single provider object and array of providers.

    Expected event structure:
    {
        "bucket": "my-configs-bucket",
        "key": "providers/config.json"
    }

    Returns:
    {
        "providers": [{...}, {...}],  # Array of provider configs
        "bucket": "...",
        "key": "..."
    }
    """
    try:
        bucket = event.get('bucket')
        key = event.get('key')

        logger.info(f"Reading config from S3: s3://{bucket}/{key}")

        if not bucket or not key:
            raise ValueError("Missing required parameters: 'bucket' and 'key'")

        # Read config from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        config_content = response['Body'].read().decode('utf-8')
        config = json.loads(config_content)

        # Handle both single object and array of objects
        if isinstance(config, dict):
            # Single provider config - convert to array
            providers = [config]
            logger.info("Config contains single provider")
        elif isinstance(config, list):
            # Array of provider configs
            providers = config
            logger.info(f"Config contains {len(providers)} providers")
        else:
            raise ValueError(
                "Config must be either an object or an array of objects")

        # Validate and enrich each provider config
        enriched_providers = []
        for idx, provider_config in enumerate(providers):
            # Validate required fields
            required_fields = ['provider', 'namespace', 'platforms']
            for field in required_fields:
                if field not in provider_config:
                    raise ValueError(
                        f"Provider {idx}: Missing required field '{field}' in config file")

            version = provider_config.get('version', 'latest')

            # Resolve "latest" version from public registry
            if version.lower() == 'latest':
                logger.info(f"Resolving 'latest' version for {provider_config['namespace']}/{provider_config['provider']}")
                version = get_latest_version(provider_config['namespace'], provider_config['provider'])
                logger.info(f"Resolved to version: {version}")

            # Enrich with extracted fields for easy access
            enriched_config = {
                'config': provider_config,
                'provider': provider_config['provider'],
                'namespace': provider_config['namespace'],
                'version': version,
                'gpg_key_id': provider_config.get('gpg-key-id'),
                'platforms': provider_config['platforms'],
                'bucket': bucket,
                'key': key
            }
            enriched_providers.append(enriched_config)
            logger.info(
                f"Validated: {provider_config['namespace']}/{provider_config['provider']} "
                f"v{version}")

        logger.info(
            f"Successfully read and validated {len(enriched_providers)} provider configs")

        return {
            'statusCode': 200,
            'providers': enriched_providers,
            'providerCount': len(enriched_providers),
            'bucket': bucket,
            'key': key
        }

    except s3_client.exceptions.NoSuchKey:
        logger.error(f"Config file not found: s3://{bucket}/{key}")
        raise Exception(f"Config file not found: s3://{bucket}/{key}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {str(e)}")
        raise Exception(f"Invalid JSON in config file: {str(e)}")
    except Exception as e:
        logger.error(f"Error reading config from S3: {str(e)}")
        raise Exception(f"Error reading config from S3: {str(e)}")


def get_latest_version(namespace: str, provider: str) -> str:
    """Get latest version from Terraform public registry."""
    url = f"https://registry.terraform.io/v1/providers/{namespace}/{provider}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()
    version = data.get("version")

    if not version:
        raise ValueError(f"No version found for {namespace}/{provider}")

    return version
