# CCDEW GitHub Actions Workflow Templates

## Purpose

Automated CI/CD workflows for CCDEW workspaces.

### ccdew-quality-gate.yml

Runs on every push/PR:
1. Evaluate setup (37 checks)
2. Run test suites
3. Check codeburn cost
4. Upload audit report

## Usage

Copy to `.github/workflows/` in your project:

```bash
cp _TEMPLATES/github-workflows/ccdew-quality-gate.yml .github/workflows/
```

## Customization

Edit the workflow to:
- Add custom test commands
- Configure branch protection rules
- Set environment variables
- Add Slack/Teams notifications