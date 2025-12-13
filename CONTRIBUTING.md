# Contributing to FX Market Microstructure Monitor

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/Real-Time-FX-Market-Microstructure-Monitor.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
5. Install dependencies: `pip install -r requirements.txt`
6. Install pre-commit hooks: `pre-commit install`

## Development Workflow

1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `pytest tests/`
4. Format code: `black src/`
5. Check linting: `pylint src/`
6. Commit your changes: `git commit -m "Add feature: description"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Create a Pull Request

## Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting (line length: 100)
- Use isort for import sorting
- Add type hints to all functions
- Write docstrings for all public methods (Google style)

## Testing

- Write unit tests for new features
- Maintain test coverage above 80%
- Run `pytest tests/ -v --cov=src` to check coverage

## Commit Messages

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Keep the first line under 72 characters
- Add detailed description if needed

Example:
```
Add WebSocket support for real-time updates

- Implemented WebSocket server
- Updated dashboard to use WebSocket
- Added connection retry logic
```

## Pull Request Process

1. Update README.md if needed
2. Update documentation
3. Ensure all tests pass
4. Request review from maintainers
5. Address review comments
6. Squash commits if requested

## Code Review

All submissions require review. We use GitHub pull requests for this purpose.

## Questions?

Open an issue or reach out to the maintainers.

Thank you for contributing! 🎉
