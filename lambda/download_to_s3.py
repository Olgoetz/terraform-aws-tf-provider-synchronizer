"""
AWS Lambda function to download provider from public registry to S3.
This Lambda is NOT in VPC to access public internet directly.
"""

import os
import logging
import boto3
import json
from typing import Dict, List
import requests

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))

# S3 client
s3_client = boto3.client('s3')


def lambda_handler(event: Dict, context) -> Dict:
    """
    Download provider from public registry to S3.
    Version is already resolved by read_config Lambda.

    Expected event structure:
    {
        "provider": "aws",
        "namespace": "hashicorp",
        "version": "6.26.0",  # Already resolved from "latest"
        "platforms": [...]
    }

    Returns:
    {
        "success": true,
        "provider": "aws",
        "version": "6.26.0",
        "s3Bucket": "...",
        "s3Prefix": "tmp/aws/6.26.0/",
        "manifestKey": "tmp/aws/6.26.0/manifest.json"
    }
    """
    try:
        # Get configuration from environment
        bucket_name = os.environ.get('S3_BUCKET_NAME')

        if not bucket_name:
            raise ValueError("Missing required environment variable: S3_BUCKET_NAME")

        provider = event['provider']
        namespace = event['namespace']
        version = event['version']  # Already resolved by read_config
        platforms = event['platforms']
        gpg_key_id = event.get('gpg_key_id')

        logger.info(f"Downloading {namespace}/{provider} v{version} to S3")
        logger.info(f"Platforms: {len(platforms)}")

        # Create S3 prefix for this provider/version
        s3_prefix = f"tmp/{provider}/{version}/"

        # Download provider files to S3
        manifest = download_provider_to_s3(
            namespace, provider, version, platforms,
            bucket_name, s3_prefix
        )

        # Add metadata to manifest
        manifest['gpg_key_id'] = gpg_key_id
        manifest['provider'] = provider
        manifest['namespace'] = namespace
        manifest['version'] = version

        # Save manifest to S3
        manifest_key = f"{s3_prefix}manifest.json"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=manifest_key,
            Body=json.dumps(manifest, indent=2),
            ContentType='application/json'
        )

        logger.info(f"Successfully downloaded {len(manifest['binaries'])} platforms to S3")
        logger.info(f"Manifest saved to s3://{bucket_name}/{manifest_key}")

        return {
            **event,
            'statusCode': 200,
            'success': True,
            's3Bucket': bucket_name,
            's3Prefix': s3_prefix,
            'manifestKey': manifest_key,
            'platformsDownloaded': len(manifest['binaries'])
        }

    except Exception as e:
        logger.error(f"Error downloading to S3: {str(e)}")
        raise Exception(f"Error downloading to S3: {str(e)}")


def download_provider_to_s3(
        namespace: str,
        provider: str,
        version: str,
        platforms: List[Dict],
        bucket: str,
        s3_prefix: str
) -> Dict:
    """Download provider files from public registry to S3."""
    logger.debug(f"Starting download for {namespace}/{provider} v{version}")
    registry_base = "https://registry.terraform.io/v1/providers"

    manifest = {
        'binaries': [],
        'shasums_key': None,
        'signature_key': None
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

        # Download binary to S3
        download_url = download_info['download_url']
        filename = f"terraform-provider-{provider}_{version}_{os_name}_{arch}.zip"
        s3_key = f"{s3_prefix}{filename}"

        download_to_s3(download_url, bucket, s3_key)

        manifest['binaries'].append({
            'os': os_name,
            'arch': arch,
            'filename': filename,
            's3_key': s3_key
        })

        # Download SHA256SUMS (only once)
        if not shasums_downloaded:
            shasums_url = download_info.get('shasums_url')
            if shasums_url:
                shasums_filename = f"terraform-provider-{provider}_{version}_SHA256SUMS"
                shasums_key = f"{s3_prefix}{shasums_filename}"
                download_to_s3(shasums_url, bucket, shasums_key)
                manifest['shasums_key'] = shasums_key
                shasums_downloaded = True

        # Download signature (only once)
        if not sig_downloaded:
            sig_url = download_info.get('shasums_signature_url')
            if sig_url:
                sig_filename = f"terraform-provider-{provider}_{version}_SHA256SUMS.sig"
                sig_key = f"{s3_prefix}{sig_filename}"
                download_to_s3(sig_url, bucket, sig_key)
                manifest['signature_key'] = sig_key
                sig_downloaded = True

    return manifest


def download_to_s3(url: str, bucket: str, s3_key: str) -> None:
    """Download a file from URL directly to S3."""
    logger.debug(f"Downloading {url} to s3://{bucket}/{s3_key}")

    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()

    # Stream directly to S3
    s3_client.upload_fileobj(
        response.raw,
        bucket,
        s3_key
    )

    logger.debug(f"Successfully uploaded to S3: {s3_key}")
