# Contributing to Hydra News

Thank you for your interest in contributing to Hydra News! This document outlines the process for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and constructive environment for everyone. We expect all contributors to adhere to these principles:

- Use inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue in the GitHub repository with the following information:

- A clear, descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Any relevant logs or screenshots
- Environment information (OS, browser, etc.)

### Suggesting Enhancements

If you have an idea for an enhancement, please create an issue with:

- A clear, descriptive title
- A detailed description of the proposed enhancement
- Why this enhancement would be valuable
- If possible, examples or mock-ups

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Run tests to ensure your changes do not break existing functionality
5. Submit a pull request with a clear description of your changes

## Development Guidelines

### Code Style

- **C Code**: Follow the [Linux kernel coding style](https://www.kernel.org/doc/html/v4.10/process/coding-style.html)
- **Go Code**: Follow the [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)
- **Python Code**: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- **TypeScript/React Code**: Follow the [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)

### Testing

- Write unit tests for all new functionality
- Ensure existing tests pass before submitting a pull request
- For cryptographic primitives, include security tests

### Documentation

- Update documentation for any changed APIs or features
- Add inline comments for complex logic
- Update the README.md if necessary

## Development Setup

To set up a development environment:

1. Clone the repository
2. Run `./scripts/start_dev.sh` to start all services
3. Make your changes
4. Test your changes
5. Submit a pull request

## Security Considerations

Since Hydra News deals with cryptographic security and source protection:

- Always consider security implications of your changes
- Do not commit sensitive keys or credentials
- Report security vulnerabilities privately to the maintainers

## License

By contributing to Hydra News, you agree that your contributions will be licensed under the same license as the project (MIT License). You should have the right to grant this license for any code you contribute.

## Project Structure

The project is organized into the following main directories:

```
hydra-news/
├── c/                  # C-based cryptographic primitives
│   └── src/            
├── go/                 # Go-based distributed consensus and API
│   └── src/            
├── python/             # Python-based content processing
│   └── src/            
├── typescript/         # TypeScript/React frontend
│   └── src/            
├── scripts/            # Build and development scripts
├── tests/              # Tests for core components
└── docs/               # Documentation
```

### Component Responsibilities

When contributing, consider the following separation of concerns:

1. **C Components**:
   - Core cryptographic algorithms
   - Performance-critical operations
   - Low-level security primitives

2. **Go Components**:
   - Distributed consensus logic
   - Identity verification and management
   - API endpoints and request handling
   - System-level operations

3. **Python Components**:
   - Content analysis and processing
   - Natural language processing tasks
   - Entity and claim extraction
   - Cross-reference verification

4. **TypeScript Components**:
   - User interface
   - Interactive visualization
   - Frontend state management
   - API integration

## Review Process

Pull requests will be reviewed by at least one project maintainer. The review process includes:

1. Code review for style and quality
2. Verification that tests pass
3. Security review for sensitive components
4. Documentation review

Once a pull request is approved, it will be merged into the main branch.

## Communication

For questions or discussions about the project:

- Use GitHub Issues for bug reports and feature requests
- Use GitHub Discussions for general questions and ideas
- For security-related concerns, contact the maintainers directly

## Acknowledgments

We appreciate all contributions to the Hydra News project. Contributors will be acknowledged in the project's README.md.

Thank you for helping to build a more trustworthy and secure news ecosystem!
