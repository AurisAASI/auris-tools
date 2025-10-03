# API Overview

Auris Tools is organized into several modules, each providing specific functionality.

## Main Components

- **Configuration** (`configuration.py`): Handles AWS configuration settings.
- **Database Handlers** (`databaseHandlers.py`): Provides interfaces for DynamoDB operations.
- **Office Word Handler** (`officeWordHandler.py`): Manages Microsoft Word document processing.
- **Storage Handler** (`storageHandler.py`): Handles AWS S3 storage operations.
- **Textract Handler** (`textractHandler.py`): Interfaces with AWS Textract for document analysis.
- **Gemini Handler** (`geminiHandler.py`): Provides integration with Google Gemini AI.
- **Utilities** (`utils.py`): Common utility functions used across the library.

## Module Dependencies

```
configuration.py <-- databaseHandlers.py, storageHandler.py, textractHandler.py
utils.py <-- (used by all modules)
```

## Detailed API Reference

For detailed documentation on each component, see the specific pages in this API reference section.