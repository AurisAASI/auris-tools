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

# Update an item
updates = {"value": 456, "status": "updated"}
updated_item = db_handler.update_item("unique-id", updates)

# Delete an item
db_handler.delete_item("unique-id")
```

### Scanning and Querying DynamoDB

The `scan` and `query` methods provide powerful ways to retrieve filtered data from DynamoDB tables.

#### Scan Operations

Scan examines every item in the table. Use filters to reduce the result set.

```python
# Scan all items
result = db_handler.scan()
all_items = result['Items']
print(f"Found {result['Count']} items")

# Scan with filters using Django-style operators
result = db_handler.scan(filters={
    'age__gte': 18,              # age >= 18
    'status__eq': 'active',       # status == 'active'
    'category__in': ['premium', 'gold']  # category in ['premium', 'gold']
})

# Scan with pagination control
result = db_handler.scan(
    filters={'verified__exists': True},
    max_items=100,                # Maximum total items to return
    page_size=50                  # Items per DynamoDB request
)

# Stream large datasets with generator (memory efficient)
for item in db_handler.scan(
    filters={'archived__eq': False},
    return_generator=True
):
    process_item(item)

# Scan with projection (only return specific attributes)
result = db_handler.scan(
    filters={'score__gt': 100},
    projection_expression='id, score, category'
)
```

#### Supported Filter Operators

```python
# Comparison operators
{'age__eq': 25}            # Equal: age == 25
{'age__ne': 25}            # Not equal: age != 25
{'age__lt': 50}            # Less than: age < 50
{'age__lte': 50}           # Less than or equal: age <= 50
{'age__gt': 18}            # Greater than: age > 18
{'age__gte': 18}           # Greater than or equal: age >= 18

# Range operator
{'age__between': [18, 65]} # Between: 18 <= age <= 65

# String operators
{'name__begins_with': 'John'}    # Name starts with 'John'
{'email__contains': '@example'}  # Email contains '@example'

# Existence operators
{'verified__exists': True}       # Attribute exists
{'deleted__exists': False}       # Attribute does not exist (using not_exists)

# List membership
{'category__in': ['A', 'B', 'C']}  # Category in list
```

#### Query Operations

Query is more efficient than scan as it uses table/index keys. **Requires partition key.**

```python
# Query by partition key
result = db_handler.query(partition_key_value='user-123')
user_items = result['Items']

# Query with additional filters
result = db_handler.query(
    partition_key_value='user-123',
    filters={'age__gte': 18, 'verified__eq': True}
)

# Query with sort key condition (if table has sort key)
from boto3.dynamodb.conditions import Key

result = db_handler.query(
    partition_key_value='user-123',
    sort_key_condition={'timestamp__gt': '2024-01-01'}
)

# Or using boto3 Key expression directly
result = db_handler.query(
    partition_key_value='user-123',
    sort_key_condition=Key('timestamp').between('2024-01-01', '2024-12-31')
)

# Query a Global Secondary Index (GSI)
result = db_handler.query(
    partition_key_value='active',
    partition_key_name='status',      # GSI partition key
    filters={'created_at__gte': '2024-01-01'},
    index_name='StatusIndex'
)

# Query with descending order (if using sort key)
result = db_handler.query(
    partition_key_value='user-123',
    scan_index_forward=False          # False = descending, True = ascending
)

# Stream query results with generator
for item in db_handler.query(
    partition_key_value='user-123',
    filters={'active__eq': True},
    return_generator=True
):
    process_item(item)
```

#### When to Use Scan vs Query

- **Use Query when:**
  - You know the partition key value
  - You need efficient lookups by key
  - You want to reduce read costs
  
- **Use Scan when:**
  - You don't know the partition key
  - You need to search across the entire table
  - You're performing full-table operations

**Note:** Query is significantly faster and more cost-effective than scan for large tables.

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