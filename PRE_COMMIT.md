# Pre-commit Configuration

This directory includes comprehensive pre-commit hooks for Terraform and Python code quality.

## Quick Start

```bash
# Install pre-commit and required tools
make install-tools
make install-hooks

# Run all checks manually
make test
```

## Installation

### 1. Install Tools

```bash
# macOS
brew install terraform tflint tfsec terraform-docs

# Install Python tools
pip install pre-commit checkov bandit flake8 autopep8 detect-secrets
```

### 2. Install Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## Available Hooks

### Terraform Hooks

- **terraform_fmt** - Format Terraform files
- **terraform_validate** - Validate Terraform configuration
- **terraform_docs** - Auto-generate documentation
- **terraform_tflint** - Lint Terraform files
- **terraform_tfsec** - Security scanning
- **terraform_checkov** - Policy as code validation

### Python Hooks (Lambda Functions)

- **autopep8** - Auto-format Python code
- **flake8** - Python linting
- **bandit** - Security vulnerability scanning

### General Hooks

- **trailing-whitespace** - Remove trailing whitespace
- **end-of-file-fixer** - Ensure files end with newline
- **check-yaml** - Validate YAML syntax
- **check-json** - Validate JSON syntax
- **detect-secrets** - Prevent secrets from being committed
- **check-merge-conflict** - Detect merge conflicts
- **detect-private-key** - Prevent private keys
- **markdownlint** - Lint Markdown files
- **shellcheck** - Validate shell scripts

## Makefile Targets

```bash
make help              # Show available targets
make install-hooks     # Install pre-commit hooks
make install-tools     # Install required tools
make fmt              # Format Terraform files
make validate         # Validate Terraform
make lint             # Run tflint
make security         # Run security scans
make python-lint      # Lint Python files
make test             # Run all checks
make docs             # Generate documentation
make clean            # Clean build artifacts
make pre-commit       # Run pre-commit on all files
```

## Configuration Files

- `.pre-commit-config.yaml` - Pre-commit hook configuration
- `.tflint.hcl` - TFLint rules and plugins
- `.markdownlint.yaml` - Markdown linting rules
- `.secrets.baseline` - Detect-secrets baseline
- `Makefile` - Automation targets

## Skipping Hooks

To skip hooks during commit (use sparingly):

```bash
# Skip all hooks
git commit --no-verify

# Skip specific hook
SKIP=terraform_tfsec git commit
```

## Updating Hooks

```bash
# Update to latest versions
pre-commit autoupdate

# Clean and reinstall
pre-commit clean
pre-commit install
```

## CI/CD Integration

Add to your CI pipeline:

```bash
make ci  # Installs hooks and runs all tests
```

## Troubleshooting

### tflint AWS plugin not found

```bash
tflint --init
```

### Terraform docs not updating

```bash
terraform-docs markdown table --output-file README.md --output-mode inject .
```

### Secrets detected

Update `.secrets.baseline`:

```bash
detect-secrets scan --baseline .secrets.baseline
```
