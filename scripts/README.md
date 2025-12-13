# GPG Key Manager for HCP Terraform

A command-line tool to manage GPG keys on HCP Terraform's private registry and fetch signing keys from the Terraform public registry.

_Disclaimer: The same operations can be use for Terraform Enterprise._

## Features

- ✅ **List** all GPG keys in your HCP Terraform organization
- ✅ **Get** details of a specific GPG key
- ✅ **Fetch** signing keys from the Terraform public registry
- ✅ **Create** (upload) new GPG keys to HCP Terraform
- ✅ **Update** existing GPG keys
- ✅ **Delete** GPG keys from your organization

## Installation

### Requirements

- Python 3.7+
- `requests` library

```bash
pip install requests
```

## Configuration

Set the following environment variables for HCP Terraform operations:

```bash
export TFC_TOKEN="your-hcp-terraform-api-token"
export TFC_ORGANIZATION="your-organization-name"

# For TFE
export TFC_API_BASE="your-tfe-address"
```

> **Note:** The `fetch` command does not require these environment variables as it only queries the public Terraform registry.

### Getting an API Token

1. Log in to [HCP Terraform](https://app.terraform.io/)
2. Go to **User Settings** → **Tokens**
3. Create a new API token
4. Set it as an environment variable: `export TFC_TOKEN="your-token"`

## Usage

```bash
python manage_gpg_keys.py <command> [options]
```

### Commands

#### List Keys

List all GPG keys in your organization:

```bash
python manage_gpg_keys.py list
```

Show detailed information:

```bash
python manage_gpg_keys.py list --verbose
```

**Example output:**

```
Found 2 GPG key(s):

1. Key ID: 34365D9472D7468F
   Namespace: my-org
   Created: 2025-01-15T10:30:00.000Z

2. Key ID: 38027F80D7FD5FB2
   Namespace: my-org
   Created: 2025-01-20T14:45:00.000Z
```

---

#### Get Key

Get detailed information about a specific GPG key:

```bash
python manage_gpg_keys.py get <KEY_ID>
```

**Example:**

```bash
python manage_gpg_keys.py get 34365D9472D7468F
```

**Example output:**

```
GPG Key Information:

Key ID:      34365D9472D7468F
Namespace:   my-org
Source:      terraform-registry
Created:     2025-01-15T10:30:00.000Z
Updated:     2025-01-15T10:30:00.000Z

ASCII Armor:
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQINBF2...
...
=txfz
-----END PGP PUBLIC KEY BLOCK-----
```

---

#### Fetch Keys from Public Registry

Fetch GPG signing keys from the Terraform public registry (no HCP credentials needed):

```bash
python manage_gpg_keys.py fetch <namespace> <provider> [options]
```

**Options:**

- `--version` - Specific provider version (defaults to latest)
- `--show-key` - Display the ASCII-armored public key
- `--output` - Save key to a file

**Examples:**

```bash
# Fetch latest version
python manage_gpg_keys.py fetch integrations github

# Fetch specific version
python manage_gpg_keys.py fetch integrations github --version 6.9.0

# Display the public key
python manage_gpg_keys.py fetch hashicorp aws --show-key

# Save to file
python manage_gpg_keys.py fetch integrations github --output github-key.asc

# Combine options
python manage_gpg_keys.py fetch hashicorp aws --show-key --output hashicorp-key.asc
```

**Example output:**

```
Fetching signing keys for integrations/github
Version: latest

Found 1 signing key(s):

1. Key ID: 38027F80D7FD5FB2
   Use --show-key to display the public key
   Use --output to save to a file
```

---

#### Create Key

Upload a new GPG key to HCP Terraform:

**From a file:**

```bash
python manage_gpg_keys.py create --file <path-to-key.asc>
```

**From GPG keyring:**

```bash
python manage_gpg_keys.py create --key-id <KEY_ID>
```

**Examples:**

```bash
# Upload from file
python manage_gpg_keys.py create --file my-signing-key.asc

# Export from local GPG keyring and upload
python manage_gpg_keys.py create --key-id 38027F80D7FD5FB2
```

**Example output:**

```
Exporting GPG key 38027F80D7FD5FB2 from keyring

Uploading GPG key to HCP Terraform...

✓ Successfully created GPG key

Key ID:      38027F80D7FD5FB2
Namespace:   my-org
Created:     2025-12-13T08:30:00.000Z
```

---

#### Update Key

Update an existing GPG key:

```bash
python manage_gpg_keys.py update <KEY_ID> [--file <path-to-key.asc>]
```

**Examples:**

```bash
# Update from file
python manage_gpg_keys.py update 38027F80D7FD5FB2 --file updated-key.asc

# Update from GPG keyring
python manage_gpg_keys.py update 38027F80D7FD5FB2
```

---

#### Delete Key

Delete a GPG key from your organization:

```bash
python manage_gpg_keys.py delete <KEY_ID> [--force]
```

**Options:**

- `-f, --force` - Skip confirmation prompt

**Examples:**

```bash
# Delete with confirmation
python manage_gpg_keys.py delete 38027F80D7FD5FB2

# Delete without confirmation
python manage_gpg_keys.py delete 38027F80D7FD5FB2 --force
```

**Example output:**

```
Are you sure you want to delete GPG key '38027F80D7FD5FB2'? (yes/no): yes
Deleting GPG key 38027F80D7FD5FB2...
✓ Successfully deleted GPG key '38027F80D7FD5FB2'
```

---

## Common Workflows

### 1. Upload a Provider's Signing Key to HCP Terraform

```bash
# Fetch the key from public registry and save it
python manage_gpg_keys.py fetch integrations github --output github-key.asc

# Upload it to your HCP Terraform organization
python manage_gpg_keys.py create --file github-key.asc
```

### 2. Use Your Own GPG Key

```bash
# Export your GPG key
gpg --armor --export YOUR_KEY_ID > my-key.asc

# Upload to HCP Terraform
python manage_gpg_keys.py create --file my-key.asc
```

### 3. List and Verify Keys

```bash
# List all keys
python manage_gpg_keys.py list

# Get details of a specific key
python manage_gpg_keys.py get 34365D9472D7468F
```

---

## File Formats

### ASCII-Armored GPG Public Key

The tool expects GPG public keys in ASCII-armored format:

```
-----BEGIN PGP PUBLIC KEY BLOCK-----

mQINBF2VUvIBEADCF4pQEZGrw...
[base64 encoded key data]
...
=txfz
-----END PGP PUBLIC KEY BLOCK-----
```

### Exporting Keys from GPG

```bash
# Export a specific key
gpg --armor --export KEY_ID > key.asc

# List keys in your keyring
gpg --list-keys
```

### Importing Keys to GPG

```bash
# Import a key file
gpg --import key.asc

# Fetch from keyserver
gpg --keyserver keyserver.ubuntu.com --recv-keys KEY_ID
```

---

## API Reference

The tool uses the following HCP Terraform API endpoints:

- **List Keys:** `GET /api/registry/private/v2/gpg-keys?filter[namespace]=ORG`
- **Get Key:** `GET /api/registry/private/v2/gpg-keys/ORG/KEY_ID`
- **Create Key:** `POST /api/registry/private/v2/gpg-keys`
- **Update Key:** `PATCH /api/registry/private/v2/gpg-keys/ORG/KEY_ID`
- **Delete Key:** `DELETE /api/registry/private/v2/gpg-keys/ORG/KEY_ID`

And the Terraform public registry endpoint:

- **Fetch Provider Keys:** `GET https://registry.terraform.io/v1/providers/NAMESPACE/PROVIDER/VERSION/download/linux/amd64`

---

## Troubleshooting

### "GPG key not found"

Make sure the key ID is correct. List all keys to verify:

```bash
python manage_gpg_keys.py list
```

### "Could not export key from GPG keyring"

The key might not be in your local GPG keyring. Import it first:

```bash
gpg --import key.asc
```

Or use the `--file` option instead:

```bash
python manage_gpg_keys.py create --file key.asc
```

### "TFC_TOKEN environment variable not set"

Set your HCP Terraform API token:

```bash
export TFC_TOKEN="your-token-here"
export TFC_ORGANIZATION="your-org-name"
```

### "Error: 401 Unauthorized"

Your API token may be invalid or expired. Generate a new one from HCP Terraform settings.

---

## Security Considerations

- **API Tokens:** Keep your `TFC_TOKEN` secure. Never commit it to version control.
- **Private Keys:** This tool only handles **public** keys. Never upload private keys.
- **Key Verification:** Always verify GPG key fingerprints before trusting them.

---

## License

This tool is provided as-is for managing GPG keys on HCP Terraform.

---

## Related Tools

- **Provider Downloader:** Download Terraform providers from the public registry
- **Provider Uploader:** Upload providers to HCP Terraform private registry

---

## Contributing

Contributions are welcome! Please ensure that:

- Code follows Python best practices
- Error handling is comprehensive
- Documentation is updated for new features
