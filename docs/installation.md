# Installation

This project requires **Python 3.10** and uses [Poetry](https://python-poetry.org/) for dependency management.

## Using Poetry (Recommended)

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

## Using pip

You can also install Auris Tools directly from PyPI:

```bash
pip install auris-tools
```

## Development Installation

If you want to contribute to Auris Tools, you should install the development dependencies:

```bash
poetry install --with dev
```

This will install all the development tools like pytest, isort, and blue for code formatting.