#!/usr/bin/env python3
"""
Manage GPG keys on HCP Terraform private registry.
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
import requests


class GPGKeyManager:
    """Manage GPG keys on HCP Terraform."""


    API_BASE = os.getenv("TFC_API_BASE", "https://app.terraform.io/api")
    REGISTRY_API_BASE = "https://registry.terraform.io/v1/providers"

    def __init__(self, token: str, organization: str):
        """
        Initialize the GPG key manager.

        Args:
            token: HCP Terraform API token
            organization: Organization name
        """
        self.token = token
        self.organization = organization
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json"
        }

    def fetch_provider_signing_keys(self, namespace: str, provider: str, version: str = None) -> List[Dict]:
        """
        Fetch signing keys from Terraform public registry.

        Args:
            namespace: Provider namespace (e.g., 'integrations', 'hashicorp')
            provider: Provider name (e.g., 'github', 'aws')
            version: Optional version (uses latest if not specified)

        Returns:
            List of signing key objects
        """
        # If no version specified, get the latest
        if not version:
            url = f"{self.REGISTRY_API_BASE}/{namespace}/{provider}"
            response = requests.get(url)
            response.raise_for_status()
            version = response.json().get("version")

        # Get download info which includes signing keys
        # We need to query with a platform, but signing keys are the same for all platforms
        url = f"{self.REGISTRY_API_BASE}/{namespace}/{provider}/{version}/download/linux/amd64"
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        return data.get("signing_keys", {}).get("gpg_public_keys", [])

    def list_keys(self) -> List[Dict]:
        """
        List all GPG keys for the organization.

        Returns:
            List of GPG key objects
        """
        url = f"{self.API_BASE}/registry/private/v2/gpg-keys"
        params = {"filter[namespace]": self.organization}
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

    def get_key(self, key_id: str) -> Optional[Dict]:
        """
        Get a specific GPG key.

        Args:
            key_id: GPG key ID

        Returns:
            GPG key object or None if not found
        """
        url = f"{self.API_BASE}/registry/private/v2/gpg-keys/{self.organization}/{key_id}"

        response = requests.get(url, headers=self.headers)

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json().get("data")

    def create_key(self, ascii_armor: str) -> Dict:
        """
        Create (upload) a new GPG key.

        Args:
            ascii_armor: ASCII armored public key

        Returns:
            Created GPG key object
        """
        url = f"{self.API_BASE}/registry/private/v2/gpg-keys"

        data = {
            "data": {
                "type": "gpg-keys",
                "attributes": {
                    "namespace": self.organization,
                    "ascii-armor": ascii_armor
                }
            }
        }

        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()

        return response.json().get("data")

    def update_key(self, key_id: str, ascii_armor: str) -> Dict:
        """
        Update an existing GPG key.

        Args:
            key_id: GPG key ID
            ascii_armor: ASCII armored public key

        Returns:
            Updated GPG key object
        """
        url = f"{self.API_BASE}/registry/private/v2/gpg-keys/{self.organization}/{key_id}"

        data = {
            "data": {
                "type": "gpg-keys",
                "attributes": {
                    "namespace": self.organization,
                    "ascii-armor": ascii_armor
                }
            }
        }

        response = requests.patch(url, headers=self.headers, json=data)
        response.raise_for_status()

        return response.json().get("data")

    def delete_key(self, key_id: str) -> bool:
        """
        Delete a GPG key.

        Args:
            key_id: GPG key ID

        Returns:
            True if successful
        """
        url = f"{self.API_BASE}/registry/private/v2/gpg-keys/{self.organization}/{key_id}"

        response = requests.delete(url, headers=self.headers)

        if response.status_code == 404:
            return False

        response.raise_for_status()
        return True


def load_gpg_key_from_file(filepath: str) -> str:
    """Load ASCII armored GPG key from file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    return path.read_text()


def export_gpg_key_from_keyring(key_id: str) -> Optional[str]:
    """Export GPG key from local keyring."""
    try:
        result = subprocess.run(
            ["gpg", "--armor", "--export", key_id],
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout:
            return result.stdout
        return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def format_key_info(key_data: Dict) -> None:
    """Pretty print GPG key information."""
    attrs = key_data.get("attributes", {})

    print(f"Key ID:      {attrs.get('key-id')}")
    print(f"Namespace:   {attrs.get('namespace')}")
    print(f"Source:      {attrs.get('source', 'N/A')}")
    print(f"Created:     {attrs.get('created-at', 'N/A')}")
    print(f"Updated:     {attrs.get('updated-at', 'N/A')}")

    # Show ASCII armor if requested
    if attrs.get('ascii-armor'):
        print(f"\nASCII Armor:")
        print(attrs['ascii-armor'])


def cmd_list(args, manager: GPGKeyManager):
    """List all GPG keys."""
    try:
        keys = manager.list_keys()

        if not keys:
            print("No GPG keys found")
            return 0

        print(f"Found {len(keys)} GPG key(s):\n")

        for i, key in enumerate(keys, 1):
            attrs = key.get("attributes", {})
            print(f"{i}. Key ID: {attrs.get('key-id')}")
            print(f"   Namespace: {attrs.get('namespace')}")
            print(f"   Created: {attrs.get('created-at', 'N/A')}")

            if args.verbose:
                print(f"   Source: {attrs.get('source', 'N/A')}")
                print(f"   Updated: {attrs.get('updated-at', 'N/A')}")

            print()

        return 0
    except requests.exceptions.HTTPError as e:
        print(f"Error listing GPG keys: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        return 1


def cmd_get(args, manager: GPGKeyManager):
    """Get a specific GPG key."""
    try:
        key = manager.get_key(args.key_id)

        if not key:
            print(f"GPG key '{args.key_id}' not found", file=sys.stderr)
            return 1

        print(f"GPG Key Information:\n")
        format_key_info(key)

        return 0
    except requests.exceptions.HTTPError as e:
        print(f"Error retrieving GPG key: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        return 1


def cmd_create(args, manager: GPGKeyManager):
    """Create (upload) a new GPG key."""
    try:
        # Load the GPG key
        ascii_armor = None

        if args.file:
            print(f"Loading GPG key from file: {args.file}")
            ascii_armor = load_gpg_key_from_file(args.file)
        elif args.key_id:
            print(f"Exporting GPG key {args.key_id} from keyring")
            ascii_armor = export_gpg_key_from_keyring(args.key_id)
            if not ascii_armor:
                print(f"Error: Could not export key {args.key_id} from GPG keyring", file=sys.stderr)
                print("Make sure the key is imported: gpg --import key.asc", file=sys.stderr)
                return 1
        else:
            print("Error: Either --file or --key-id must be specified", file=sys.stderr)
            return 1

        # Create the key
        print(f"\nUploading GPG key to HCP Terraform...")
        result = manager.create_key(ascii_armor)

        print(f"\n✓ Successfully created GPG key\n")
        format_key_info(result)

        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except requests.exceptions.HTTPError as e:
        print(f"Error creating GPG key: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        return 1


def cmd_update(args, manager: GPGKeyManager):
    """Update an existing GPG key."""
    try:
        # Load the GPG key
        ascii_armor = None

        if args.file:
            print(f"Loading GPG key from file: {args.file}")
            ascii_armor = load_gpg_key_from_file(args.file)
        else:
            print(f"Exporting GPG key {args.key_id} from keyring")
            ascii_armor = export_gpg_key_from_keyring(args.key_id)
            if not ascii_armor:
                print(f"Error: Could not export key {args.key_id} from GPG keyring", file=sys.stderr)
                print("Specify --file to load from a file instead", file=sys.stderr)
                return 1

        # Update the key
        print(f"\nUpdating GPG key {args.key_id} on HCP Terraform...")
        result = manager.update_key(args.key_id, ascii_armor)

        print(f"\n✓ Successfully updated GPG key\n")
        format_key_info(result)

        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except requests.exceptions.HTTPError as e:
        print(f"Error updating GPG key: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        return 1


def cmd_delete(args, manager: GPGKeyManager):
    """Delete a GPG key."""
    # Confirm deletion
    if not args.force:
        response = input(f"Are you sure you want to delete GPG key '{args.key_id}'? (yes/no): ")
        if response.lower() != "yes":
            print("Deletion cancelled")
            return 0

    try:
        print(f"Deleting GPG key {args.key_id}...")
        success = manager.delete_key(args.key_id)

        if not success:
            print(f"GPG key '{args.key_id}' not found", file=sys.stderr)
            return 1

        print(f"✓ Successfully deleted GPG key '{args.key_id}'")
        return 0
    except requests.exceptions.HTTPError as e:
        print(f"Error deleting GPG key: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        return 1


def cmd_fetch(args, manager: GPGKeyManager):
    """Fetch GPG signing keys from Terraform public registry."""
    try:
        print(f"Fetching signing keys for {args.namespace}/{args.provider}")
        if args.version:
            print(f"Version: {args.version}")
        else:
            print(f"Version: latest")

        keys = manager.fetch_provider_signing_keys(args.namespace, args.provider, args.version)

        if not keys:
            print(f"No signing keys found for {args.namespace}/{args.provider}", file=sys.stderr)
            return 1

        print(f"\nFound {len(keys)} signing key(s):\n")

        for i, key in enumerate(keys, 1):
            key_id = key.get("key_id")
            ascii_armor = key.get("ascii_armor")

            print(f"{i}. Key ID: {key_id}")

            if args.show_key:
                print(f"\nPublic Key:")
                print(ascii_armor)
                print()

            # Save to file if requested
            if args.output:
                if len(keys) == 1:
                    filename = args.output
                else:
                    # Multiple keys, append key_id to filename
                    base = Path(args.output)
                    filename = f"{base.stem}_{key_id}{base.suffix}"

                Path(filename).write_text(ascii_armor)
                print(f"✓ Saved to: {filename}")

            if not args.show_key and not args.output:
                print(f"   Use --show-key to display the public key")
                print(f"   Use --output to save to a file")

            print()

        return 0
    except requests.exceptions.HTTPError as e:
        print(f"Error fetching signing keys: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manage GPG keys on HCP Terraform private registry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  TFC_TOKEN         HCP Terraform API token (required for HCP operations)
  TFC_ORGANIZATION  HCP Terraform organization name (required for HCP operations)

Examples:
  # List all GPG keys
  %(prog)s list

  # Get details of a specific key
  %(prog)s get 34365D9472D7468F

  # Fetch signing keys from Terraform registry
  %(prog)s fetch integrations github
  %(prog)s fetch integrations github --version 6.9.0
  %(prog)s fetch integrations github --show-key
  %(prog)s fetch integrations github --output github-key.asc

  # Create a new key from file
  %(prog)s create --file my-key.asc

  # Create a new key from GPG keyring
  %(prog)s create --key-id 34365D9472D7468F

  # Update an existing key
  %(prog)s update 34365D9472D7468F --file updated-key.asc

  # Delete a key
  %(prog)s delete 34365D9472D7468F
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    subparsers.required = True

    # List command
    list_parser = subparsers.add_parser('list', help='List all GPG keys')
    list_parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed information')
    list_parser.set_defaults(func=cmd_list)

    # Get command
    get_parser = subparsers.add_parser('get', help='Get a specific GPG key')
    get_parser.add_argument('key_id', help='GPG key ID')
    get_parser.set_defaults(func=cmd_get)

    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch GPG signing keys from Terraform public registry')
    fetch_parser.add_argument('namespace', help='Provider namespace (e.g., integrations, hashicorp)')
    fetch_parser.add_argument('provider', help='Provider name (e.g., github, aws)')
    fetch_parser.add_argument('--version', help='Provider version (defaults to latest)')
    fetch_parser.add_argument('--show-key', action='store_true', help='Display the public key')
    fetch_parser.add_argument('--output', help='Save key to file')
    fetch_parser.set_defaults(func=cmd_fetch)

    # Create command
    create_parser = subparsers.add_parser('create', help='Create (upload) a new GPG key')
    create_group = create_parser.add_mutually_exclusive_group(required=True)
    create_group.add_argument('--file', help='Path to ASCII armored GPG key file')
    create_group.add_argument('--key-id', help='GPG key ID to export from local keyring')
    create_parser.set_defaults(func=cmd_create)

    # Update command
    update_parser = subparsers.add_parser('update', help='Update an existing GPG key')
    update_parser.add_argument('key_id', help='GPG key ID to update')
    update_parser.add_argument('--file', help='Path to ASCII armored GPG key file (if not specified, exports from keyring)')
    update_parser.set_defaults(func=cmd_update)

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a GPG key')
    delete_parser.add_argument('key_id', help='GPG key ID to delete')
    delete_parser.add_argument('-f', '--force', action='store_true', help='Skip confirmation prompt')
    delete_parser.set_defaults(func=cmd_delete)

    args = parser.parse_args()

    # Get credentials from environment (not required for fetch command)
    token = os.environ.get("TFC_TOKEN")
    organization = os.environ.get("TFC_ORGANIZATION")

    # For fetch command, we don't need HCP credentials
    if args.command == 'fetch':
        # Create a minimal manager just for the fetch operation
        manager = GPGKeyManager(token or "", organization or "")
        exit_code = args.func(args, manager)
        sys.exit(exit_code)

    # For other commands, require credentials
    if not token:
        print("Error: TFC_TOKEN environment variable not set", file=sys.stderr)
        print("Set it with: export TFC_TOKEN=your-token-here", file=sys.stderr)
        sys.exit(1)

    if not organization:
        print("Error: TFC_ORGANIZATION environment variable not set", file=sys.stderr)
        print("Set it with: export TFC_ORGANIZATION=your-org-name", file=sys.stderr)
        sys.exit(1)

    # Initialize manager
    manager = GPGKeyManager(token, organization)

    # Execute command
    exit_code = args.func(args, manager)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
