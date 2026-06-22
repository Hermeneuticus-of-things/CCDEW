# Contributing to CCDEW

Thank you for your interest in CCDEW! This project is a universal AI agent ecosystem framework.

## How to Contribute

### Reporting Issues
- Check existing issues before creating a new one
- Use a clear, descriptive title
- Include steps to reproduce, expected behavior, and actual behavior
- Include relevant logs, screenshots, or code snippets

### Submitting Changes
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run the tests (`node .claude/helpers/tests/*.test.cjs`)
5. Commit with a clear message
6. Push and open a Pull Request

### Code Style
- **JavaScript/Node.js**: ES2020+, CommonJS modules, use `node -c` to validate syntax
- **Python**: Python 3.10+, PEP 8 style, use `py_compile` to validate
- **Mermaid**: Keep diagrams readable; use ASCII-safe characters in labels
- **README**: All documentation must be in English
- **Tests**: New features should include tests in `.claude/helpers/tests/`

### Commit Messages
Use conventional commits: `type: description`
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `test:` testing
- `refactor:` code restructuring
- `chore:` maintenance

### Pull Request Process
1. Ensure all tests pass
2. Update README.md if needed
3. Add or update tests for your changes
4. Your PR will be reviewed by a maintainer

## Code of Conduct
Be respectful, constructive, and inclusive. Harassment and toxic behavior will not be tolerated.
