# Test Fixtures

All test data in this directory is **synthetic** — programmatically generated with no
connection to real users, clients, or production systems.

## Provenance

- All fixtures are created by test helper functions using `pandas` and random/numeric data
- No file in this directory was exported from any analytics platform, email system,
  or production environment
- No PII, PHI, credentials, or proprietary business metrics exist in any fixture

## Adding new fixtures

1. Generate synthetic data in a test helper or conftest fixture
2. Do NOT copy, export, or derive fixtures from real GA4, Drive, or email data
3. Document the generation logic in the relevant test module
4. Ensure filenames don't suggest real client or project names
