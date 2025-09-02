# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
- Run unit tests: `pytest tests`
- Run all tests (including integration): `pytest tests --large`
- Run integration tests: `pytest tests/integration/ --integration`  
- Testing uses pytest with black code formatting checks: `pytest tests --black`
- Always use venv like uv whenever possible or venv as a fallback

### Integration Testing Requirements
Integration tests are located in `tests/integration/` and require a Databricks workspace.

**Required Setup:**
1. Configure Databricks CLI profile: `databricks configure --profile your-profile-name`
2. Set environment variables:
   - **DATABRICKS_CONFIG_PROFILE**: Databricks CLI profile name (required)
   - **DATABRICKS_CLOUD**: Cloud provider - `aws`, `azure`, or `gcp` (required)
   - **TEST_CATALOG_NAME**: Unity Catalog name for UC tests (optional, defaults to "test")
   - **TEST_SCHEMA_NAME**: Schema name for tests (optional, defaults to "mlops_stacks_integration_tests")

**Example Usage:**
```bash
# AWS integration tests
DATABRICKS_CONFIG_PROFILE=e2demo-aws DATABRICKS_CLOUD=aws pytest tests/integration/ --integration

# Azure integration tests  
DATABRICKS_CONFIG_PROFILE=e2demo-azure DATABRICKS_CLOUD=azure pytest tests/integration/ --integration

# Skip cleanup for debugging
SKIP_CLEANUP=1 DATABRICKS_CONFIG_PROFILE=e2demo-aws DATABRICKS_CLOUD=aws pytest tests/integration/ --integration
```

⚠️ **CRITICAL SECURITY WARNING**: 
- **NEVER echo, print, or log authentication tokens or credentials**
- **NEVER include tokens in command lines that may be logged**
- Always use environment variables for sensitive data (DATABRICKS_HOST, DATABRICKS_TOKEN)
- The Databricks CLI automatically reads from environment variables - no need to configure with tokens via echo

**IMPORTANT**: Never assume Unity Catalog settings. Always ask and confirm:
- Whether UC is enabled in the workspace
- Which catalog name to use for testing
- Which schema name to use for testing
- Whether the test user has appropriate UC permissions

### GitHub Actions Integration Tests

The repository includes automated nightly integration tests via GitHub Actions in `.github/workflows/integration-tests.yaml`.

**Required GitHub Secrets:**
- **DATABRICKS_HOST_AWS**: AWS workspace URL (e.g., `https://your-workspace.cloud.databricks.com`)
- **DATABRICKS_TOKEN_AWS**: Personal Access Token for AWS workspace  
- **DATABRICKS_HOST_AZURE**: Azure workspace URL (e.g., `https://adb-xxxx.xx.azuredatabricks.net`)
- **DATABRICKS_TOKEN_AZURE**: Personal Access Token for Azure workspace
- **NOTIFICATION_EMAIL_USERNAME**: Gmail username for failure notifications (optional)
- **NOTIFICATION_EMAIL_PASSWORD**: Gmail app password for notifications (optional)
- **NOTIFICATION_EMAIL_TO**: Email address to receive failure notifications (optional)

**Optional GitHub Variables:**
- **TEST_CATALOG_NAME**: Unity Catalog name (defaults to `main_integration_tests`)
- **TEST_SCHEMA_NAME**: Schema name (defaults to `gha_integration_tests`)

**Workflow Features:**
- **Schedule**: Runs nightly at 2 AM UTC
- **Manual Trigger**: Can be run manually via GitHub UI
- **Parallel Execution**: AWS and Azure tests run in parallel
- **Retry Logic**: Automatically retries flaky tests twice
- **Artifacts**: Uploads test results and logs
- **Email Notifications**: Sends email on failure (if configured)
- **Status Checks**: Creates commit status showing integration test results

### Development Setup
- Install development requirements: `pip install -r dev-requirements.txt`
- Required external dependencies: actionlint, databricks CLI, npm, act
- Python 3.8+ required

### Project Generation
- Initialize new MLOps project: `databricks bundle init mlops-stacks`
- Preview changes using example configs: Use files in `tests/example-project-configs/`

## Architecture Overview

### Repository Structure
This is a Databricks MLOps Stacks template repository that generates production-ready ML projects via Databricks asset bundle templates.

**Core Components:**
- `template/`: Contains parameterized project templates with `.tmpl` files
- `databricks_template_schema.json`: Defines project initialization parameters and validation
- `library/`: Template helper functions and variable definitions
- `tests/`: Unit and integration tests for template generation
- `conftest.py`: Pytest configuration with large test markers

### Template System
- Uses Go text templating with parameters like `{{.input_project_name}}`
- Templates generate complete ML projects with CI/CD, training, and inference code
- Supports multiple cloud providers (Azure, AWS, GCP) and CI/CD platforms (GitHub Actions, Azure DevOps, GitLab)

### Generated Project Structure
Generated projects contain:
- **ML Code**: Training pipelines, batch inference, feature engineering
- **Resources**: Databricks bundle configurations for ML jobs and workflows
- **CI/CD**: Automated testing and deployment workflows
- **Monitoring**: Model performance monitoring and alerting

### Key Template Areas
- `template/{{.input_root_dir}}/{{template 'project_name_alphanumeric_underscore' .}}/training/`: ML training code and notebooks
- `template/{{.input_root_dir}}/{{template 'project_name_alphanumeric_underscore' .}}/resources/`: Databricks resource definitions
- `template/{{.input_root_dir}}/{{template 'project_name_alphanumeric_underscore' .}}/deployment/`: Model deployment and batch inference
- `template/{{.input_root_dir}}/.github/`: GitHub Actions workflows

### Testing Strategy
- Template generation tests in `test_create_project.py`
- CI/CD workflow validation in `test_github_actions.py`, `test_gitlab.py`
- Bundle resource validation in `test_bundle_resources.py`
- Large tests run actual project generation and validation

### Unity Catalog Cleanup Commands
For integration test cleanup of UC resources created during testing:
- **Registered Models**: `databricks registered-models delete CATALOG.SCHEMA.MODEL_NAME` (NOT `databricks models`)
- **Tables**: `databricks tables delete CATALOG.SCHEMA.TABLE_NAME` (NOT `databricks unity-catalog tables delete`)
- **Batch Inference Output**: The predictions table is named `predictions` in the schema: `CATALOG.SCHEMA.predictions`

### Integration Test Best Practices

⚠️ **AVOID REDUNDANT INTEGRATION TESTS**:

**Common Anti-patterns to Avoid:**
1. **Separate project creation per test** - Creates duplicate infrastructure, slow execution
2. **Multiple validate/deploy cycles** - Each test doing its own bundle validate/deploy/destroy
3. **Jobs API usage** - Avoid `databricks jobs list`, `databricks experiments list` - use `bundle summary` instead
4. **Feature-specific tests that only do basic validate/deploy** - If a test only validates that "Feature X projects can deploy", it's likely redundant

**Preferred Patterns:**
1. **Shared fixtures** - Use session-scoped fixtures for project creation and deployment
2. **Comprehensive validation** - One fixture that validates, another that deploys, tests that verify specific functionality
3. **Bundle commands only** - Prefer `bundle run`, `bundle summary`, `bundle validate` over Jobs/Experiments APIs
4. **Fixture dependencies** - Ensure validation runs before deployment via fixture dependencies
5. **Single cleanup** - Consolidate all cleanup in the final fixture

**Before Adding Integration Tests, Ask:**
- Does this test create its own project? (❌ Bad - use shared fixtures)
- Does this test only do validate/deploy without testing specific functionality? (❌ Redundant)
- Does this test use Jobs API instead of bundle commands? (❌ Slow and flaky)
- Could this be covered by parametrized tests with different feature flags? (✅ Better)
- Does this test verify unique functionality not covered elsewhere? (✅ Good)

**Examples of Good vs Bad Tests:**
- ❌ `test_unity_catalog_integration()` - Creates separate UC project, only does validate/deploy
- ❌ `test_feature_store_integration()` - Creates separate FS project, only does validate/deploy  
- ✅ `test_bundle_run_job_execution()` - Uses shared deployment, tests ALL jobs via bundle run
- ✅ `test_bundle_resource_creation()` - Uses shared deployment, verifies deployed resources have URLs

## Important Notes

- This repository generates other repositories - avoid modifying generated code here
- Template changes require testing with example project configurations
- CI/CD workflows are tested with `act` for GitHub Actions simulation
- All generated projects follow MLOps best practices with dev/staging/prod environments