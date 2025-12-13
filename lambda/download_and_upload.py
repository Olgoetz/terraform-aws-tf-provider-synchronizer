"""
AWS Lambda function to download provider from public registry and upload to HCP Terraform.
This must be a single Lambda to avoid sharing binaries between steps.
"""

import os
import logging
import boto3
import tempfile
import hashlib
from pathlib import Path
from typing import Dict, List
import requests

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
    Download provider from public registry and upload to HCP Terraform.

    Expected event structure:
    {
        "config": {...},
        "provider": "aws",
        "namespace": "hashicorp",
        "resolvedVersion": "6.26.0",
        "gpg_key_id": "...",
        "platforms": [...]
    }

    Returns:
    {
        "success": true,
        "provider": "aws",
        "version": "6.26.0",
        "platformsUploaded": 5,
        "registryUrl": "https://app.terraform.io/..."
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
        original_namespace = event['namespace']
        version = event['resolvedVersion']
        gpg_key_id = event.get('gpg_key_id')
        platforms = event['platforms']

        logger.info(
            f"Starting download and upload for {original_namespace}/{provider} v{version}")
        logger.info(f"Platforms: {len(platforms)}")

        # Create temp directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Download provider files
            logger.info(
                f"Downloading {original_namespace}/{provider} v{version}")
            downloaded_files = download_provider(
                original_namespace, provider, version, platforms, temp_path
            )
            logger.info(
                f"Downloaded {len(downloaded_files['binaries'])} platform binaries")

            # Upload to HCP Terraform / Terraform Enterprise
            logger.info(
                f"Uploading to organization: {organization} at {tfc_address}")
            upload_result = upload_to_hcp(
                organization, provider, version, gpg_key_id,
                downloaded_files, token, tfc_address
            )

            logger.info(
                f"Successfully uploaded {upload_result['platforms_count']} platforms")

            return {
                'statusCode': 200,
                'success': True,
                'provider': provider,
                'namespace': original_namespace,
                'version': version,
                'platformsUploaded': upload_result['platforms_count'],
                'registryUrl': (
                    f"{tfc_address}/app/{organization}/registry/private/providers/"
                    f"{organization}/{provider}/{version}")}

    except Exception as e:
        logger.error(f"Error in download/upload process: {str(e)}")
        raise Exception(f"Error in download/upload process: {str(e)}")


def download_provider(namespace: str, provider: str, version: str,
                      platforms: List[Dict], output_dir: Path) -> Dict:
    """Download provider files from public registry."""
    logger.debug(f"Starting download for {namespace}/{provider} v{version}")
    registry_base = "https://registry.terraform.io/v1/providers"
    files = {
        'binaries': [],
        'shasums': None,
        'signature': None
    }

    shasums_downloaded = False
    sig_downloaded = False

    for platform in platforms:
        os_name = platform['os']
        arch = platform['arch']
        logger.debug(f"Downloading binary for {os_name}/{arch}")

        # Get download info
        url = f"{registry_base}/{namespace}/{provider}/{version}/download/{os_name}/{arch}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        download_info = response.json()

        # Download binary
        download_url = download_info['download_url']
        filename = f"terraform-provider-{provider}_{version}_{os_name}_{arch}.zip"
        filepath = output_dir / filename

        download_file(download_url, filepath)

        files['binaries'].append({
            'os': os_name,
            'arch': arch,
            'filename': filename,
            'path': filepath
        })

        # Download SHA256SUMS (only once)
        if not shasums_downloaded:
            shasums_url = download_info.get('shasums_url')
            if shasums_url:
                shasums_path = output_dir / \
                    f"terraform-provider-{provider}_{version}_SHA256SUMS"
                download_file(shasums_url, shasums_path)
                files['shasums'] = shasums_path
                shasums_downloaded = True

        # Download signature (only once)
        if not sig_downloaded:
            sig_url = download_info.get('shasums_signature_url')
            if sig_url:
                sig_path = output_dir / \
                    f"terraform-provider-{provider}_{version}_SHA256SUMS.sig"
                download_file(sig_url, sig_path)
                files['signature'] = sig_path
                sig_downloaded = True

    return files


def download_file(url: str, filepath: Path) -> None:
    """Download a file from URL."""
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()

    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


def upload_to_hcp(organization: str, provider: str, version: str,
                  gpg_key_id: str, files: Dict, token: str,
                  tfc_address: str = 'https://app.terraform.io') -> Dict:
    """Upload provider to HCP Terraform or Terraform Enterprise."""
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
        organization,
        provider,
        version,
        gpg_key_id,
        headers,
        tfc_address)

    # Upload SHA256SUMS and signature
    shasums_upload_url = version_data['data']['links']['shasums-upload']
    shasums_sig_upload_url = version_data['data']['links']['shasums-sig-upload']

    upload_file_to_url(files['shasums'], shasums_upload_url)
    upload_file_to_url(files['signature'], shasums_sig_upload_url)

    # Upload binaries
    platforms_uploaded = 0
    for binary_info in files['binaries']:
        shasum = calculate_shasum(binary_info['path'])

        # Create platform
        platform_data = create_platform(
            organization, provider, version,
            binary_info['os'], binary_info['arch'],
            binary_info['filename'], shasum, headers, tfc_address
        )

        # Upload binary
        binary_upload_url = platform_data['data']['links']['provider-binary-upload']
        upload_file_to_url(binary_info['path'], binary_upload_url)
        platforms_uploaded += 1

    return {
        'platforms_count': platforms_uploaded
    }


def check_provider_exists(
        organization: str,
        provider: str,
        headers: Dict,
        tfc_address: str = 'https://app.terraform.io') -> bool:
    """Check if provider exists."""
    url = f"{tfc_address}/api/v2/organizations/{organization}/registry-providers/private/{organization}/{provider}"
    response = requests.get(url, headers=headers, timeout=10)
    return response.status_code == 200


def create_provider(organization: str, provider: str, headers: Dict,
                    tfc_address: str = 'https://app.terraform.io') -> None:
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
    response = requests.post(url, headers=headers, json=data, timeout=10)
    response.raise_for_status()


def create_version(organization: str, provider: str, version: str,
                   key_id: str, headers: Dict,
                   tfc_address: str = 'https://app.terraform.io') -> Dict:
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
    response = requests.post(url, headers=headers, json=data, timeout=10)
    response.raise_for_status()
    return response.json()


def create_platform(organization: str, provider: str, version: str,
                    os_name: str, arch: str, filename: str, shasum: str,
                    headers: Dict,
                    tfc_address: str = 'https://app.terraform.io') -> Dict:
    """Create platform."""
    url = (
        f"{tfc_address}/api/v2/organizations/{organization}/"
        f"registry-providers/private/{organization}/{provider}/versions/{version}/platforms")
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
    response = requests.post(url, headers=headers, json=data, timeout=10)
    response.raise_for_status()
    return response.json()


def upload_file_to_url(filepath: Path, url: str) -> None:
    """Upload file to presigned URL."""
    with open(filepath, 'rb') as f:
        response = requests.put(url, data=f, timeout=300)
        response.raise_for_status()


def calculate_shasum(filepath: Path) -> str:
    """Calculate SHA256 hash of file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
