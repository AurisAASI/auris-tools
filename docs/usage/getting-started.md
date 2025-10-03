# Getting Started

This guide will help you get started with Auris Tools.

## Basic Usage

First, import the modules you need:

```python
from auris_tools.configuration import AWSConfiguration
from auris_tools.databaseHandlers import DatabaseHandler
from auris_tools.storageHandler import StorageHandler
```

## Configuration

Create an AWS configuration:

```python
config = AWSConfiguration()
```

## Working with DynamoDB

```python
# Initialize a database handler
db_handler = DatabaseHandler(table_name="your-table", config=config)

# Insert an item
item = {
    "id": "unique-id",
    "name": "Test Item",
    "value": 123
}
db_handler.insert_item(item)

# Retrieve an item
key = {"id": "unique-id"}
retrieved_item = db_handler.get_item(key)
```

## Working with S3 Storage

```python
# Initialize a storage handler
storage_handler = StorageHandler(bucket_name="your-bucket", config=config)

# Upload a file
storage_handler.upload_file("/path/to/local/file.txt", "remote/path/file.txt")

# Download a file
storage_handler.download_file("remote/path/file.txt", "/path/to/local/file.txt")
```

For more detailed examples, see the specific documentation for each module.