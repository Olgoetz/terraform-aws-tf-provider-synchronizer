.PHONY: help init fmt validate docs lint security install-hooks test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install-hooks: ## Install pre-commit hooks
	@echo "Installing pre-commit hooks..."
	@pip install pre-commit
	@pre-commit install
	@pre-commit install --hook-type commit-msg
	@echo "✓ Pre-commit hooks installed"

install-tools: ## Install required tools (tflint, tfsec, checkov, etc.)
	@echo "Installing required tools..."
	@command -v terraform >/dev/null 2>&1 || { echo "Error: terraform not found"; exit 1; }
	@command -v tflint >/dev/null 2>&1 || brew install tflint
	@command -v trivy >/dev/null 2>&1 || brew install trivy
	@command -v terraform-docs >/dev/null 2>&1 || brew install terraform-docs
	@pip install bandit flake8 autopep8 detect-secrets
	@echo "✓ Tools installed"

init: ## Initialize Terraform
	@echo "Initializing Terraform..."
	@terraform init
	@echo "✓ Terraform initialized"

fmt: ## Format Terraform files
	@echo "Formatting Terraform files..."
	@terraform fmt -recursive
	@echo "✓ Terraform files formatted"

validate: init ## Validate Terraform configuration
	@echo "Validating Terraform configuration..."
	@terraform validate
	@echo "✓ Terraform configuration valid"

docs: ## Generate Terraform documentation
	@echo "Generating Terraform documentation..."
	@terraform-docs markdown table --output-file README.md --output-mode inject .
	@echo "✓ Documentation generated"

lint: ## Run tflint
	@echo "Running tflint..."
	@tflint --init
	@tflint --config .tflint.hcl
	@echo "✓ Linting complete"

security: ## Run security scans (tfsec and checkov)
	@echo "Running tfsec..."
	@tfsec . --concise-output
	@echo "Running checkov..."
	@checkov -d . --quiet --framework terraform --skip-check CKV_AWS_18,CKV_AWS_144,CKV2_AWS_5
	@echo "✓ Security scans complete"

python-lint: ## Lint Python Lambda functions
	@echo "Linting Python files..."
	@flake8 lambda/ --max-line-length=120 --extend-ignore=E203,W503
	@bandit -r lambda/ -ll
	@echo "✓ Python linting complete"

test: fmt validate lint security python-lint ## Run all tests
	@echo "✓ All tests passed"

plan: validate ## Run Terraform plan
	@terraform plan

apply: validate ## Run Terraform apply
	@terraform apply

clean: ## Clean up build artifacts
	@echo "Cleaning up..."
	@rm -rf builds/
	@rm -rf lambda/layer/python/
	@rm -rf .terraform/
	@rm -f .terraform.lock.hcl
	@echo "✓ Cleaned up"

pre-commit: ## Run pre-commit on all files
	@pre-commit run --all-files

ci: install-hooks test ## Run CI pipeline (install hooks and run tests)
	@echo "✓ CI pipeline complete"
