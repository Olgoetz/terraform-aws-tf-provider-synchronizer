"""
AWS Lambda function to check if provider version exists on HCP Terraform.
"""

import os
import logging
import boto3
import requests
from typing import Dict

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))

# Secrets Manager client
secretsmanager = boto3.client('secretsmanager')


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

    Expected event structure:
    {
        "config": {...},
        "provider": "aws",
        "namespace": "hashicorp",
        "version": "6.26.0" or "latest",
        ...
    }

    Returns:
    {
        "versionExists": true/false,
        "resolvedVersion": "6.26.0",
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
        version = event['version']

        logger.info(f"Checking version for {namespace}/{provider} v{version}")

        # Resolve version if it's "latest"
        resolved_version = version
        if version.lower() == "latest":
            logger.info(
                f"Resolving 'latest' version for {namespace}/{provider}")
            resolved_version = get_latest_version(namespace, provider)
            logger.info(f"Resolved version: {resolved_version}")

        # Check if version exists on HCP/TFE
        logger.info(
            f"Checking if {organization}/{provider} v{resolved_version} exists on {tfc_address}")
        version_exists = check_version_on_hcp(
            organization, provider, resolved_version, token, tfc_address
        )
        logger.info(
            f"Version exists: {version_exists}, should process: {not version_exists}")

        # Add results to event
        return {
            **event,
            'versionExists': version_exists,
            'resolvedVersion': resolved_version,
            'shouldProcess': not version_exists,
            'statusCode': 200
        }

    except Exception as e:
        logger.error(f"Error checking HCP version: {str(e)}")
        raise Exception(f"Error checking HCP version: {str(e)}")


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

    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code == 200
    except Exception:
        return False
