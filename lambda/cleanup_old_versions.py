"""
AWS Lambda function to clean up old provider versions from HCP Terraform/TFE.
Keeps the most recent N versions and deletes older ones.
"""

import os
import logging
import json
import boto3
import requests
from typing import Dict, List

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# AWS clients
secretsmanager = boto3.client('secretsmanager')


def get_secret(secret_name: str) -> str:
    """Retrieve secret from AWS Secrets Manager."""
    try:
        response = secretsmanager.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except Exception as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {str(e)}")
        raise


def list_providers(
        organization: str,
        token: str,
        tfc_address: str = 'https://app.terraform.io') -> List[Dict]:
    """List all private providers in the organization."""
    url = (
        f"{tfc_address}/api/v2/organizations/{organization}/"
        f"registry-providers"
    )
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/vnd.api+json'
    }

    providers = []
    while url:
        logger.info(f"Fetching providers from: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        providers.extend(data.get('data', []))

        # Handle pagination
        next_page = data.get('links', {}).get('next')
        url = f"{tfc_address}{next_page}" if next_page else None

    logger.info(f"Found {len(providers)} providers")
    return providers


def list_provider_versions(
        organization: str,
        registry_name: str,
        namespace: str,
        provider: str,
        token: str,
        tfc_address: str = 'https://app.terraform.io') -> List[Dict]:
    """List all versions for a specific provider."""
    url = (
        f"{tfc_address}/api/v2/organizations/{organization}/"
        f"registry-providers/{registry_name}/{namespace}/{provider}/versions"
    )
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/vnd.api+json'
    }

    versions = []
    while url:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        versions.extend(data.get('data', []))

        # Handle pagination
        next_page = data.get('links', {}).get('next')
        url = f"{tfc_address}{next_page}" if next_page else None

    return versions


def delete_provider_version(
        organization: str,
        registry_name: str,
        namespace: str,
        provider: str,
        version: str,
        token: str,
        tfc_address: str = 'https://app.terraform.io') -> bool:
    """Delete a specific provider version."""
    url = (
        f"{tfc_address}/api/v2/organizations/{organization}/"
        f"registry-providers/{registry_name}/{namespace}/{provider}/"
        f"versions/{version}"
    )
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/vnd.api+json'
    }

    try:
        response = requests.delete(url, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info(
            f"Deleted version {version} of provider {provider}"
        )
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(
                f"Version {version} of provider {provider} not found"
            )
            return False
        logger.error(
            f"Failed to delete version {version} of provider {provider}: "
            f"{str(e)}"
        )
        raise


def parse_version(version_string: str) -> tuple:
    """Parse semantic version string into comparable tuple."""
    try:
        parts = version_string.lstrip('v').split('.')
        return tuple(int(p) for p in parts)
    except (ValueError, AttributeError):
        logger.warning(f"Could not parse version: {version_string}")
        return (0, 0, 0)


def cleanup_provider_versions(
        organization: str,
        registry_name: str,
        namespace: str,
        provider: str,
        keep_count: int,
        token: str,
        tfc_address: str = 'https://app.terraform.io',
        dry_run: bool = False) -> Dict:
    """Clean up old versions of a provider, keeping the most recent N."""
    logger.info(
        f"Cleaning up provider {registry_name}/{namespace}/{provider}, "
        f"keeping {keep_count} versions"
    )

    # Get all versions
    versions = list_provider_versions(
        organization, registry_name, namespace, provider, token, tfc_address
    )

    if len(versions) <= keep_count:
        logger.info(
            f"Provider {provider} has {len(versions)} versions, "
            f"no cleanup needed"
        )
        return {
            'provider': provider,
            'total_versions': len(versions),
            'deleted_versions': [],
            'kept_versions': [v['attributes']['version'] for v in versions]
        }

    # Sort versions by semantic version (newest first)
    sorted_versions = sorted(
        versions,
        key=lambda v: parse_version(v['attributes']['version']),
        reverse=True
    )

    # Determine which versions to keep and delete
    versions_to_keep = sorted_versions[:keep_count]
    versions_to_delete = sorted_versions[keep_count:]

    kept_version_strings = [
        v['attributes']['version'] for v in versions_to_keep
    ]
    deleted_version_strings = []

    logger.info(
        f"Keeping versions: {', '.join(kept_version_strings)}"
    )
    logger.info(
        f"Deleting {len(versions_to_delete)} old versions"
    )

    # Delete old versions
    for version in versions_to_delete:
        version_string = version['attributes']['version']
        if dry_run:
            logger.info(
                f"[DRY RUN] Would delete version {version_string} "
                f"of provider {registry_name}/{namespace}/{provider}"
            )
            deleted_version_strings.append(version_string)
        else:
            try:
                delete_provider_version(
                    organization, registry_name, namespace, provider,
                    version_string, token, tfc_address
                )
                deleted_version_strings.append(version_string)
            except Exception as e:
                logger.error(
                    f"Failed to delete version {version_string}: {str(e)}"
                )

    return {
        'provider': provider,
        'total_versions': len(versions),
        'deleted_versions': deleted_version_strings,
        'kept_versions': kept_version_strings,
        'deleted_count': len(deleted_version_strings)
    }


def lambda_handler(event, context):
    """Lambda handler for cleaning up old provider versions."""
    logger.info(f"Cleanup event: {json.dumps(event)}")

    # Get configuration from environment variables
    secret_name = os.environ['TFC_TOKEN_SECRET_NAME']
    organization = os.environ['TFC_ORGANIZATION']
    tfc_address = os.environ.get('TFC_ADDRESS', 'https://app.terraform.io')
    keep_count = int(os.environ.get('KEEP_VERSION_COUNT', '10'))
    dry_run = os.environ.get('DRY_RUN', 'false').lower() == 'true'

    # Get TFC token from Secrets Manager
    token = get_secret(secret_name)

    # Get optional provider filter from event
    provider_filter = event.get('provider', None)

    try:
        # Get all providers or specific provider
        if provider_filter:
            logger.info(f"Cleaning up specific provider: {provider_filter}")
            # For filtered provider, assume private registry
            results = [
                cleanup_provider_versions(
                    organization,
                    'private',
                    organization,
                    provider_filter,
                    keep_count,
                    token,
                    tfc_address,
                    dry_run
                )
            ]
        else:
            logger.info("Cleaning up all providers")
            providers = list_providers(organization, token, tfc_address)

            results = []
            for provider_data in providers:
                provider_name = provider_data['attributes']['name']
                # Extract registry-name and namespace from attributes
                registry_name = provider_data['attributes'].get(
                    'registry-name', 'private'
                )
                namespace = provider_data['attributes'].get(
                    'namespace', organization
                )
                try:
                    result = cleanup_provider_versions(
                        organization,
                        registry_name,
                        namespace,
                        provider_name,
                        keep_count,
                        token,
                        tfc_address,
                        dry_run
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(
                        f"Failed to cleanup provider {provider_name}: "
                        f"{str(e)}"
                    )
                    results.append({
                        'provider': provider_name,
                        'error': str(e)
                    })

        # Calculate summary
        total_deleted = sum(
            r.get('deleted_count', 0) for r in results if 'error' not in r
        )
        total_providers = len(results)
        providers_cleaned = len(
            [r for r in results if r.get('deleted_count', 0) > 0]
        )

        summary = {
            'status': 'success',
            'dry_run': dry_run,
            'keep_count': keep_count,
            'total_providers_checked': total_providers,
            'providers_cleaned': providers_cleaned,
            'total_versions_deleted': total_deleted,
            'results': results
        }

        logger.info(
            f"Cleanup complete: {total_deleted} versions deleted "
            f"across {providers_cleaned} providers"
        )

        return summary

    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }
