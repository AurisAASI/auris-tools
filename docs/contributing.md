# Contributing

Thank you for considering contributing to Auris Tools!

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AurisAASI/auris-tools.git
   cd auris-tools
   ```

2. **Install Poetry (if not already installed):**
   ```bash
   pip install poetry
   ```

3. **Install development dependencies:**
   ```bash
   poetry install --with dev
   ```

## Running Tests

We use `pytest` for testing. To run the tests:

```bash
task test
```

## Code Style

We use `blue` (a more permissive version of Black) and `isort` for code formatting:

```bash
task lint
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-new-feature`)
3. Make your changes
4. Run tests (`task test`)
5. Format your code (`task lint`)
6. Commit your changes (`git commit -am 'Add some feature'`)
7. Push to the branch (`git push origin feature/my-new-feature`)
8. Create a new Pull Request

## Code Coverage

We aim to maintain high test coverage. Check coverage with:

```bash
task test
```

This will generate a coverage report in `htmlcov/index.html`.

## Documentation

Please update the documentation for any changes you make. We use MkDocs with the Material theme:

```bash
pip install mkdocs mkdocs-material mkdocstrings mkdocstrings-python
mkdocs serve
```

This will start a local documentation server at http://localhost:8000.