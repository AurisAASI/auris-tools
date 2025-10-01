# auris-tools

The swiss knife tools to coordinates cloud frameworks with an easy for Auris platforms

## Installation

This project requires **Python 3.10** and uses [Poetry](https://python-poetry.org/) for dependency management.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AurisAASI/auris-tools.git
   cd auris-tools
   ```
2. **Install Poetry (if not already installed):**
   ```bash
   pip install poetry
   ```
3. **Install dependencies:**
   ```bash
   poetry install
   ```

---

## Project Structure

The main classes and modules are organized as follows:

```
/auris_tools
├── __init__.py
├── configuration.py         # AWS configuration utilities
├── databaseHandlers.py      # DynamoDB handler class
├── officeWordHandler.py     # Office Word document handler
├── storageHandler.py        # AWS S3 storage handler
├── textractHandler.py       # AWS Textract handler
├── utils.py                 # Utility functions
├── geminiHandler.py         # Google Gemini AI handler
```

---

## Testing & Linting

- **Run all tests:**
  ```bash
  task test
  ```
- **Run linter (ruff):**
  ```bash
  task lint
  ```

Test coverage and linting are enforced in CI. Make sure all tests pass and code is linted before submitting a PR.

---
