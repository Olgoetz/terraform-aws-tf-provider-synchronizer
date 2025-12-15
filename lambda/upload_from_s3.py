"""
AWS Lambda function to upload provider from S3 to HCP Terraform.
This Lambda runs in VPC and reads from S3 via VPC endpoint.
"""

import os
import logging
import boto3
import json
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, Optional
import requests

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))

# AWS clients
secretsmanager = boto3.client('secretsmanager')
s3_client = boto3.client('s3')

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
    Upload provider from S3 to HCP Terraform.

    Expected event structure:
    {
        "s3Bucket": "...",
        "manifestKey": "tmp/aws/6.26.0/manifest.json",
        ...
    }

    Returns:
    {
        "success": true,
        "provider": "aws",
        "version": "6.26.0",
        "platformsUploaded": 5
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
        logger.debug(f"Retrieving TFC token from Secrets Manager: {secret_name}")
        token = get_secret(secret_name)

        bucket = event['s3Bucket']
        manifest_key = event['manifestKey']

        # Download and parse manifest
        logger.info(f"Reading manifest from s3://{bucket}/{manifest_key}")
        manifest_obj = s3_client.get_object(Bucket=bucket, Key=manifest_key)
        manifest = json.loads(manifest_obj['Body'].read().decode('utf-8'))

        provider = manifest['provider']
        version = manifest['version']
        gpg_key_id = manifest['gpg_key_id']

        logger.info(f"Uploading {provider} v{version} to {organization} at {tfc_address}")

        # Upload to HCP Terraform
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            upload_result = upload_to_hcp(
                organization, provider, version, gpg_key_id,
                manifest, bucket, token, tfc_address, temp_path
            )

        logger.info(f"Successfully uploaded {upload_result['platforms_count']} platforms")

        return {
            **event,
            'statusCode': 200,
            'success': True,
            'provider': provider,
            'version': version,
            'platformsUploaded': upload_result['platforms_count'],
            'registryUrl': (
                f"{tfc_address}/app/{organization}/registry/private/providers/"
                f"{organization}/{provider}/{version}"
            )
        }

    except Exception as e:
        logger.error(f"Error uploading from S3: {str(e)}")
        raise Exception(f"Error uploading from S3: {str(e)}")


def upload_to_hcp(
        organization: str,
        provider: str,
        version: str,
        gpg_key_id: str,
        manifest: Dict,
        bucket: str,
        token: str,
        tfc_address: str,
        temp_path: Path
) -> Dict:
    """Upload provider to HCP Terraform from S3."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.api+json"
    }

    # Check if provider exists
    provider_exists = check_provider_exists(
        organization, provider, headers, tfc_address)

    # Create provider if needed
    if not provider_exists:
        create_provider(organization, provider, headers, tfc_address)

    # Create version
    version_data = create_version(
        organization, provider, version, gpg_key_id,
        headers, tfc_address
    )

    # Download and upload SHA256SUMS and signature from S3
    shasums_upload_url = version_data['data']['links']['shasums-upload']
    shasums_sig_upload_url = version_data['data']['links']['shasums-sig-upload']

    shasums_path = temp_path / "SHA256SUMS"
    sig_path = temp_path / "SHA256SUMS.sig"

    s3_client.download_file(bucket, manifest['shasums_key'], str(shasums_path))
    s3_client.download_file(bucket, manifest['signature_key'], str(sig_path))

    upload_file_to_url(shasums_path, shasums_upload_url)
    upload_file_to_url(sig_path, shasums_sig_upload_url)

    # Upload binaries
    platforms_uploaded = 0
    for binary_info in manifest['binaries']:
        # Download binary from S3 to temp
        binary_path = temp_path / binary_info['filename']
        s3_client.download_file(bucket, binary_info['s3_key'], str(binary_path))

        shasum = calculate_shasum(binary_path)

        # Create platform
        platform_data = create_platform(
            organization, provider, version,
            binary_info['os'], binary_info['arch'],
            binary_info['filename'], shasum, headers, tfc_address
        )

        # Upload binary
        binary_upload_url = platform_data['data']['links']['provider-binary-upload']
        upload_file_to_url(binary_path, binary_upload_url)
        platforms_uploaded += 1

    return {
        'platforms_count': platforms_uploaded
    }


def check_provider_exists(
        organization: str,
        provider: str,
        headers: Dict,
        tfc_address: str
) -> bool:
    """Check if provider exists."""
    url = f"{tfc_address}/api/v2/organizations/{organization}/registry-providers/private/{organization}/{provider}"
    ca_bundle = get_ca_bundle_path()
    verify = ca_bundle if ca_bundle else True
    response = requests.get(url, headers=headers, timeout=10, verify=verify)
    return response.status_code == 200


def create_provider(
        organization: str,
        provider: str,
        headers: Dict,
        tfc_address: str
) -> None:
    """Create provider."""
    url = f"{tfc_address}/api/v2/organizations/{organization}/registry-providers"
    data = {
        "data": {
            "type": "registry-providers",
            "attributes": {
                "name": provider,
                "namespace": organization,
                "registry-name": "private"
            }
        }
    }
    ca_bundle = get_ca_bundle_path()
    verify = ca_bundle if ca_bundle else True
    response = requests.post(url, headers=headers, json=data, timeout=10, verify=verify)
    response.raise_for_status()


def create_version(
        organization: str,
        provider: str,
        version: str,
        key_id: str,
        headers: Dict,
        tfc_address: str
) -> Dict:
    """Create provider version."""
    url = (
        f"{tfc_address}/api/v2/organizations/{organization}/"
        f"registry-providers/private/{organization}/{provider}/versions"
    )
    data = {
        "data": {
            "type": "registry-provider-versions",
            "attributes": {
                "version": version,
                "key-id": key_id,
                "protocols": ["5.0", "6.0"]
            }
        }
    }
    ca_bundle = get_ca_bundle_path()
    verify = ca_bundle if ca_bundle else True
    response = requests.post(url, headers=headers, json=data, timeout=10, verify=verify)
    response.raise_for_status()
    return response.json()


def create_platform(
        organization: str,
        provider: str,
        version: str,
        os_name: str,
        arch: str,
        filename: str,
        shasum: str,
        headers: Dict,
        tfc_address: str
) -> Dict:
    """Create platform."""
    url = (
        f"{tfc_address}/api/v2/organizations/{organization}/"
        f"registry-providers/private/{organization}/{provider}/versions/{version}/platforms"
    )
    data = {
        "data": {
            "type": "registry-provider-version-platforms",
            "attributes": {
                "os": os_name,
                "arch": arch,
                "shasum": shasum,
                "filename": filename
            }
        }
    }
    ca_bundle = get_ca_bundle_path()
    verify = ca_bundle if ca_bundle else True
    response = requests.post(url, headers=headers, json=data, timeout=10, verify=verify)
    response.raise_for_status()
    return response.json()


def upload_file_to_url(
        filepath: Path,
        url: str
) -> None:
    """Upload file to presigned URL."""
    ca_bundle = get_ca_bundle_path()
    verify = ca_bundle if ca_bundle else True
    with open(filepath, 'rb') as f:
        response = requests.put(url, data=f, timeout=300, verify=verify)
        response.raise_for_status()


def calculate_shasum(filepath: Path) -> str:
    """Calculate SHA256 hash of file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
