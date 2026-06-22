# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in CCDEW, please report it privately.

**Do not** disclose it publicly until it has been addressed.

### How to Report
- Open a draft [GitHub Security Advisory](https://github.com/Hermeneuticus-of-things/CCDEW/security/advisories)
- Or email the maintainers directly

### What to Include
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a timeline for the fix.

## Security Features

- **Secret scanning**: Pre-commit hooks detect exposed credentials
- **Permission guard**: Bash commands are validated before execution
- **Vault encryption**: Sensitive data is encrypted with PIN + biometric access
- **3 sensitivity levels**: PUBLIC / PRIVATE / SECRET — AI agents have restricted access

## Responsible Disclosure
We appreciate researchers who follow responsible disclosure practices. Thank you for helping keep CCDEW and its users safe.
