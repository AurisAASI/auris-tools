import logging

import boto3
from boto3.dynamodb.conditions import Attr, Key
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError

from auris_tools.configuration import AWSConfiguration
from auris_tools.utils import generate_uuid

# Operator mapping for filter expressions
OPERATOR_MAP = {
    'eq': lambda attr, val: Attr(attr).eq(val),
    'ne': lambda attr, val: Attr(attr).ne(val),
    'lt': lambda attr, val: Attr(attr).lt(val),
    'lte': lambda attr, val: Attr(attr).lte(val),
    'gt': lambda attr, val: Attr(attr).gt(val),
    'gte': lambda attr, val: Attr(attr).gte(val),
    'between': lambda attr, val: Attr(attr).between(val[0], val[1]),
    'begins_with': lambda attr, val: Attr(attr).begins_with(val),
    'contains': lambda attr, val: Attr(attr).contains(val),
    'exists': lambda attr, val: Attr(attr).exists()
    if val
    else Attr(attr).not_exists(),
    'in': lambda attr, val: Attr(attr).is_in(val),
}


class DatabaseHandler:
    def __init__(self, table_name, config=None):
        """
        Initialize the database handler.

        Args:
            table_name: Name of the DynamoDB table.
            config: An AWSConfiguration object, or None to use environment variables.
        """
        self.table_name = table_name
        if config is None:
            config = AWSConfiguration()

        # Create a boto3 session with the configuration
        session = boto3.session.Session(**config.get_boto3_session_args())

        # Create a DynamoDB client with additional configuration if needed
        self.client = session.client('dynamodb', **config.get_client_args())

        # Import the ConditionExpressionBuilder for building expressions
        from boto3.dynamodb.conditions import ConditionExpressionBuilder

        self._condition_builder = ConditionExpressionBuilder()

        if not self._check_table_exists(table_name):
            raise Exception(f'Table does not exist: {table_name}')

        logging.info(f'Initialized DynamoDB client in region {config.region}')

    def insert_item(self, item, primary_key: str = 'id'):
        """Insert an item with automatic type conversion"""
        if not isinstance(item, dict):
            raise TypeError('Item must be a dictionary')

        if primary_key not in item:
            item[primary_key] = generate_uuid()

        dynamo_item = self._serialize_item(item)
        response = self.client.put_item(
            TableName=self.table_name, Item=dynamo_item
        )
        return response

    def get_item(self, key):
        """
        Retrieve an item from a DynamoDB table.

        Args:
            key: A dictionary representing the key of the item to retrieve.

        Returns:
            The retrieved item, or None if not found.
        """
        if not isinstance(key, dict):
            raise TypeError('Key must be a dictionary')

        # Check if the key is in DynamoDB format (i.e., values are dicts with type keys)
        if not all(isinstance(v, dict) and len(v) == 1 for v in key.values()):
            # Convert to DynamoDB format
            key = self._serialize_item(key)

        try:
            response = self.client.get_item(TableName=self.table_name, Key=key)
            return response.get('Item')
        except Exception as e:
            logging.error(
                f'Error retrieving item from {self.table_name}: {str(e)}'
            )
            return None

    def delete_item(self, key, primary_key='id'):
        """
        Delete an item from a DynamoDB table.

        Args:
            key (str or dict): Either a string identifier for the primary key,
                              or a dictionary containing the complete key structure.
            primary_key (str, optional): Name of the primary key field. Defaults to 'id'.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        # Convert string key to a dictionary with the primary key
        if isinstance(key, str):
            key = {primary_key: key}
        elif not isinstance(key, dict):
            raise TypeError('Key must be a string identifier or a dictionary')

        # Check if the key is in DynamoDB format
        if not self.item_is_serialized(key):
            key = self._serialize_item(key)

        try:
            self.client.delete_item(
                TableName=self.table_name,
                Key=key,
                ReturnValues='ALL_OLD',  # Return the deleted item
            )
            logging.info(f'Deleted item from {self.table_name} with key {key}')
            return True
        except Exception as e:
            logging.error(
                f'Error deleting item from {self.table_name}: {str(e)}'
            )
            return False

    def update_item(self, key, updates, primary_key='id'):
        """
        Update an item in a DynamoDB table.

        This method first verifies that the item exists by checking the primary key,
        then updates or adds the specified attributes.

        Args:
            key (str or dict): Either a string identifier for the primary key,
                              or a dictionary containing the complete key structure.
            updates (dict): Dictionary of attributes to update or add to the item.
            primary_key (str, optional): Name of the primary key field. Defaults to 'id'.

        Returns:
            dict: The updated item attributes.

        Raises:
            TypeError: If key is not a string or dictionary, or if updates is not a dictionary.
            ValueError: If the item with the specified key does not exist in the table.
        """
        # Convert string key to a dictionary with the primary key
        if isinstance(key, str):
            key_dict = {primary_key: key}
        elif isinstance(key, dict):
            key_dict = key.copy()
        else:
            raise TypeError('Key must be a string identifier or a dictionary')

        if not isinstance(updates, dict):
            raise TypeError('Updates must be a dictionary')

        if not updates:
            raise ValueError('Updates dictionary cannot be empty')

        # Check if the key is in DynamoDB format
        if not self.item_is_serialized(key_dict):
            serialized_key = self._serialize_item(key_dict)
        else:
            serialized_key = key_dict

        # Verify that the item exists
        try:
            response = self.client.get_item(
                TableName=self.table_name, Key=serialized_key
            )
            if 'Item' not in response:
                raise ValueError(
                    f'Item with key {key_dict} does not exist in table {self.table_name}'
                )
        except self.client.exceptions.ResourceNotFoundException:
            raise ValueError(
                f'Item with key {key_dict} does not exist in table {self.table_name}'
            )
        except Exception as e:
            logging.error(
                f'Error checking item existence in {self.table_name}: {str(e)}'
            )
            raise

        # Build the update expression
        update_expression_parts = []
        expression_attribute_names = {}
        expression_attribute_values = {}

        for idx, (attr_name, attr_value) in enumerate(updates.items()):
            # Skip if trying to update primary key
            if attr_name == primary_key or (
                isinstance(key_dict, dict) and attr_name in key_dict
            ):
                logging.warning(
                    f'Skipping update for key attribute: {attr_name}'
                )
                continue

            # Use placeholders to handle reserved words and special characters
            attr_placeholder = f'#attr{idx}'
            value_placeholder = f':val{idx}'

            update_expression_parts.append(
                f'{attr_placeholder} = {value_placeholder}'
            )
            expression_attribute_names[attr_placeholder] = attr_name
            expression_attribute_values[
                value_placeholder
            ] = self._serialize_item({attr_name: attr_value})[attr_name]

        if not update_expression_parts:
            raise ValueError(
                'No valid attributes to update (cannot update key attributes)'
            )

        update_expression = 'SET ' + ', '.join(update_expression_parts)

        # Perform the update
        try:
            response = self.client.update_item(
                TableName=self.table_name,
                Key=serialized_key,
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues='ALL_NEW',
            )
            logging.info(
                f'Updated item in {self.table_name} with key {key_dict}'
            )
            return self._deserialize_item(response['Attributes'])
        except Exception as e:
            logging.error(
                f'Error updating item in {self.table_name}: {str(e)}'
            )
            raise

    def item_is_serialized(self, item):
        """Check if an item is in DynamoDB serialized format"""
        return all(isinstance(v, dict) and len(v) == 1 for v in item.values())

    def _serialize_item(self, item):
        """Convert Python types to DynamoDB format"""
        serializer = TypeSerializer()
        return {k: serializer.serialize(v) for k, v in item.items()}

    def _deserialize_item(self, item):
        """Convert DynamoDB format back to Python types"""
        deserializer = TypeDeserializer()
        return {k: deserializer.deserialize(v) for k, v in item.items()}

    def _check_table_exists(self, table_name):
        """Check if a DynamoDB table exists"""
        try:
            existing_tables = self.client.list_tables().get('TableNames', [])
            return table_name in existing_tables
        except Exception as e:
            logging.error(f'Error checking table existence: {str(e)}')
            return False

    def _build_expression_params(
        self, condition_expression, is_key_condition=False
    ):
        """
        Build expression parameters for DynamoDB client API.

        Converts boto3 condition expressions to the format required by the low-level client.

        Args:
            condition_expression: A boto3 condition expression (Key or Attr).
            is_key_condition (bool): True if this is a key condition expression.

        Returns:
            dict: Dictionary with expression string, attribute names, and attribute values.
        """
        if condition_expression is None:
            return {}

        # Build the expression using the condition builder
        built_expression = self._condition_builder.build_expression(
            condition_expression, is_key_condition=is_key_condition
        )

        result = {
            'expression_string': built_expression.condition_expression,
        }

        if built_expression.attribute_name_placeholders:
            result[
                'expression_attribute_names'
            ] = built_expression.attribute_name_placeholders

        if built_expression.attribute_value_placeholders:
            # Serialize attribute values for DynamoDB client
            serializer = TypeSerializer()
            result['expression_attribute_values'] = {
                k: serializer.serialize(v)
                for k, v in built_expression.attribute_value_placeholders.items()
            }

        return result

    def _build_filter_expression(self, filters):
        """
        Build a filter expression from a dictionary of filters.

        Supports Django-style operator syntax using double underscores.
        For example: {'age__gt': 18, 'status__eq': 'active'}

        Args:
            filters (dict or boto3 condition): Dictionary with field__operator keys,
                                               or a boto3 condition expression.

        Returns:
            boto3 condition expression or None if filters is empty.

        Examples:
            {'status__eq': 'active'} -> Attr('status').eq('active')
            {'age__gte': 18, 'verified__exists': True} -> Combined with AND
        """
        if filters is None:
            return None

        # If already a boto3 condition expression, return as-is
        if not isinstance(filters, dict):
            return filters

        if not filters:
            return None

        filter_expr = None

        for key, value in filters.items():
            # Check if key uses operator syntax (field__operator)
            if '__' in key:
                parts = key.rsplit('__', 1)
                if len(parts) == 2:
                    attr_name, operator = parts
                    if operator in OPERATOR_MAP:
                        condition = OPERATOR_MAP[operator](attr_name, value)
                    else:
                        # If not a valid operator, treat entire key as attribute name with eq
                        condition = Attr(key).eq(value)
                else:
                    # No operator found, use equality
                    condition = Attr(key).eq(value)
            else:
                # No operator syntax, default to equality
                condition = Attr(key).eq(value)

            # Combine conditions with AND logic
            if filter_expr is None:
                filter_expr = condition
            else:
                filter_expr = filter_expr & condition

        return filter_expr

    def _build_key_condition(
        self, partition_key_name, partition_key_value, sort_key_condition=None
    ):
        """
        Build a key condition expression for query operations.

        Args:
            partition_key_name (str): Name of the partition key attribute.
            partition_key_value: Value for the partition key (exact match).
            sort_key_condition (dict or boto3 Key condition, optional): Sort key condition.
                Can be a boto3 Key() expression or a dict with operator syntax.

        Returns:
            boto3 Key condition expression.

        Examples:
            _build_key_condition('id', 'user123') -> Key('id').eq('user123')
            _build_key_condition('id', 'user123', Key('timestamp').gt('2024-01-01'))
        """
        # Build partition key condition (always equality)
        key_expr = Key(partition_key_name).eq(partition_key_value)

        # Add sort key condition if provided
        if sort_key_condition is not None:
            # If it's a dict with operator syntax, build the condition
            if isinstance(sort_key_condition, dict):
                for key, value in sort_key_condition.items():
                    if '__' in key:
                        parts = key.rsplit('__', 1)
                        if len(parts) == 2:
                            attr_name, operator = parts
                            if operator in OPERATOR_MAP:
                                # Use Key() instead of Attr() for sort key
                                if operator == 'eq':
                                    sort_expr = Key(attr_name).eq(value)
                                elif operator == 'lt':
                                    sort_expr = Key(attr_name).lt(value)
                                elif operator == 'lte':
                                    sort_expr = Key(attr_name).lte(value)
                                elif operator == 'gt':
                                    sort_expr = Key(attr_name).gt(value)
                                elif operator == 'gte':
                                    sort_expr = Key(attr_name).gte(value)
                                elif operator == 'between':
                                    sort_expr = Key(attr_name).between(
                                        value[0], value[1]
                                    )
                                elif operator == 'begins_with':
                                    sort_expr = Key(attr_name).begins_with(
                                        value
                                    )
                                else:
                                    # Unsupported operator for sort key
                                    sort_expr = Key(attr_name).eq(value)
                                key_expr = key_expr & sort_expr
                                break
                    else:
                        # No operator, use equality
                        sort_expr = Key(key).eq(value)
                        key_expr = key_expr & sort_expr
                        break
            else:
                # Assume it's already a boto3 Key condition
                key_expr = key_expr & sort_key_condition

        return key_expr

    def _validate_index(self, index_name):
        """
        Validate that an index exists on the table.

        Args:
            index_name (str): Name of the index to validate.

        Raises:
            ValueError: If the index does not exist on the table.
        """
        try:
            response = self.client.describe_table(TableName=self.table_name)
            table_info = response.get('Table', {})

            # Collect all index names
            index_names = []

            # Global Secondary Indexes
            gsi_list = table_info.get('GlobalSecondaryIndexes', [])
            index_names.extend([gsi['IndexName'] for gsi in gsi_list])

            # Local Secondary Indexes
            lsi_list = table_info.get('LocalSecondaryIndexes', [])
            index_names.extend([lsi['IndexName'] for lsi in lsi_list])

            if index_name not in index_names:
                available = ', '.join(index_names) if index_names else 'none'
                error_msg = (
                    f"Index '{index_name}' does not exist on table '{self.table_name}'. "
                    f'Available indexes: {available}'
                )
                logging.error(error_msg)
                raise ValueError(error_msg)

        except ValueError:
            raise
        except Exception as e:
            logging.error(f'Error validating index {index_name}: {str(e)}')
            raise

    def scan(
        self,
        filters=None,
        index_name=None,
        projection_expression=None,
        max_items=None,
        page_size=None,
        return_generator=False,
    ):
        """
        Scan table with optional filters.

        Scans examine every item in the table. Use query() when possible for better performance.

        Args:
            filters (dict or boto3 condition, optional): Filters to apply. Can be a dict with
                Django-style operator syntax (e.g., {'age__gte': 18, 'status__eq': 'active'})
                or a boto3 condition expression.
            index_name (str, optional): Name of a Global or Local Secondary Index to scan.
            projection_expression (str, optional): Comma-separated list of attributes to return.
            max_items (int, optional): Maximum number of items to return. None means no limit.
            page_size (int, optional): Number of items per page (controls DynamoDB request size).
            return_generator (bool, optional): If True, returns a generator yielding items one-by-one.
                If False, returns all results in a dict. Defaults to False.

        Returns:
            If return_generator=False: dict with 'Items', 'Count', 'ScannedCount', and optionally 'LastEvaluatedKey'.
            If return_generator=True: generator yielding deserialized items.

        Raises:
            ValueError: If index_name is provided but does not exist.

        Examples:
            # Scan all items
            result = db.scan()

            # Scan with filters
            result = db.scan(filters={'status__eq': 'active', 'age__gte': 18})

            # Stream large dataset
            for item in db.scan(filters={'archived__eq': False}, return_generator=True):
                process(item)
        """
        # Validate index if provided
        if index_name:
            self._validate_index(index_name)

        # Build filter expression
        filter_expr = self._build_filter_expression(filters)

        # Build scan parameters
        scan_params = {'TableName': self.table_name}

        if index_name:
            scan_params['IndexName'] = index_name

        if filter_expr is not None:
            # Build expression params for client API
            expr_params = self._build_expression_params(filter_expr)
            scan_params['FilterExpression'] = expr_params['expression_string']
            if 'expression_attribute_names' in expr_params:
                scan_params['ExpressionAttributeNames'] = expr_params[
                    'expression_attribute_names'
                ]
            if 'expression_attribute_values' in expr_params:
                scan_params['ExpressionAttributeValues'] = expr_params[
                    'expression_attribute_values'
                ]

        if projection_expression:
            scan_params['ProjectionExpression'] = projection_expression

        if page_size:
            scan_params['Limit'] = page_size

        # Generator mode
        if return_generator:
            return self._scan_generator(scan_params, max_items)

        # Standard mode - collect all items
        all_items = []
        total_count = 0
        total_scanned = 0
        last_evaluated_key = None

        try:
            while True:
                if last_evaluated_key:
                    scan_params['ExclusiveStartKey'] = last_evaluated_key

                response = self.client.scan(**scan_params)

                items = response.get('Items', [])
                for item in items:
                    all_items.append(self._deserialize_item(item))
                    total_count += 1

                    if max_items and total_count >= max_items:
                        break

                total_scanned += response.get('ScannedCount', 0)
                last_evaluated_key = response.get('LastEvaluatedKey')

                if not last_evaluated_key or (
                    max_items and total_count >= max_items
                ):
                    break

            logging.info(
                f'Scanned {total_scanned} items from {self.table_name}, '
                f'returned {total_count} items after filtering'
            )

            result = {
                'Items': all_items,
                'Count': total_count,
                'ScannedCount': total_scanned,
            }

            if last_evaluated_key:
                result['LastEvaluatedKey'] = last_evaluated_key

            return result

        except Exception as e:
            logging.error(f'Error scanning {self.table_name}: {str(e)}')
            raise

    def _scan_generator(self, scan_params, max_items):
        """
        Generator for scanning items one at a time.

        Args:
            scan_params (dict): Parameters for the scan operation.
            max_items (int, optional): Maximum number of items to yield.

        Yields:
            Deserialized items from the scan.
        """
        items_yielded = 0
        last_evaluated_key = None

        try:
            while True:
                if last_evaluated_key:
                    scan_params['ExclusiveStartKey'] = last_evaluated_key

                response = self.client.scan(**scan_params)

                for item in response.get('Items', []):
                    yield self._deserialize_item(item)
                    items_yielded += 1

                    if max_items and items_yielded >= max_items:
                        return

                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break

        except Exception as e:
            logging.error(
                f'Error in scan generator for {self.table_name}: {str(e)}'
            )
            raise

    def query(
        self,
        partition_key_value,
        partition_key_name='id',
        sort_key_condition=None,
        filters=None,
        index_name=None,
        projection_expression=None,
        max_items=None,
        page_size=None,
        scan_index_forward=True,
        return_generator=False,
    ):
        """
        Query items using partition key and optional filters.

        Query is more efficient than scan as it uses table/index keys. Requires partition key.

        Args:
            partition_key_value: Value for the partition key (required).
            partition_key_name (str, optional): Name of the partition key attribute. Defaults to 'id'.
            sort_key_condition (dict or boto3 Key condition, optional): Condition for sort key.
                Can be a boto3 Key() expression or dict with operator syntax like {'timestamp__gt': '2024-01-01'}.
            filters (dict or boto3 condition, optional): Additional filters to apply after key condition.
                Uses same syntax as scan() filters.
            index_name (str, optional): Name of Global or Local Secondary Index to query.
            projection_expression (str, optional): Comma-separated list of attributes to return.
            max_items (int, optional): Maximum number of items to return. None means no limit.
            page_size (int, optional): Number of items per page (controls DynamoDB request size).
            scan_index_forward (bool, optional): True for ascending order, False for descending.
                Defaults to True.
            return_generator (bool, optional): If True, returns a generator yielding items.
                If False, returns all results in a dict. Defaults to False.

        Returns:
            If return_generator=False: dict with 'Items', 'Count', 'ScannedCount', and optionally 'LastEvaluatedKey'.
            If return_generator=True: generator yielding deserialized items.

        Raises:
            ValueError: If index_name is provided but does not exist.

        Examples:
            # Query by partition key
            result = db.query(partition_key_value='user123')

            # Query with sort key condition
            result = db.query(
                partition_key_value='user123',
                sort_key_condition={'timestamp__gt': '2024-01-01'}
            )

            # Query GSI with filters
            result = db.query(
                partition_key_value='active',
                partition_key_name='status',
                filters={'age__gte': 18},
                index_name='StatusIndex'
            )
        """
        # Validate index if provided
        if index_name:
            self._validate_index(index_name)

        # Build key condition
        key_condition = self._build_key_condition(
            partition_key_name, partition_key_value, sort_key_condition
        )

        # Build filter expression
        filter_expr = self._build_filter_expression(filters)

        # Build query parameters - start with key condition
        key_expr_params = self._build_expression_params(
            key_condition, is_key_condition=True
        )

        query_params = {
            'TableName': self.table_name,
            'KeyConditionExpression': key_expr_params['expression_string'],
            'ScanIndexForward': scan_index_forward,
        }

        if 'expression_attribute_names' in key_expr_params:
            query_params['ExpressionAttributeNames'] = key_expr_params[
                'expression_attribute_names'
            ]
        if 'expression_attribute_values' in key_expr_params:
            query_params['ExpressionAttributeValues'] = key_expr_params[
                'expression_attribute_values'
            ]

        if index_name:
            query_params['IndexName'] = index_name

        if filter_expr is not None:
            # Build filter expression params
            filter_expr_params = self._build_expression_params(filter_expr)
            query_params['FilterExpression'] = filter_expr_params[
                'expression_string'
            ]

            # Merge attribute names and values (if any conflicts, filter takes precedence)
            if 'expression_attribute_names' in filter_expr_params:
                if 'ExpressionAttributeNames' not in query_params:
                    query_params['ExpressionAttributeNames'] = {}
                query_params['ExpressionAttributeNames'].update(
                    filter_expr_params['expression_attribute_names']
                )

            if 'expression_attribute_values' in filter_expr_params:
                if 'ExpressionAttributeValues' not in query_params:
                    query_params['ExpressionAttributeValues'] = {}
                query_params['ExpressionAttributeValues'].update(
                    filter_expr_params['expression_attribute_values']
                )

        if projection_expression:
            query_params['ProjectionExpression'] = projection_expression

        if page_size:
            query_params['Limit'] = page_size

        # Generator mode
        if return_generator:
            return self._query_generator(query_params, max_items)

        # Standard mode - collect all items
        all_items = []
        total_count = 0
        total_scanned = 0
        last_evaluated_key = None

        try:
            while True:
                if last_evaluated_key:
                    query_params['ExclusiveStartKey'] = last_evaluated_key

                response = self.client.query(**query_params)

                items = response.get('Items', [])
                for item in items:
                    all_items.append(self._deserialize_item(item))
                    total_count += 1

                    if max_items and total_count >= max_items:
                        break

                total_scanned += response.get('ScannedCount', 0)
                last_evaluated_key = response.get('LastEvaluatedKey')

                if not last_evaluated_key or (
                    max_items and total_count >= max_items
                ):
                    break

            logging.info(
                f'Queried {total_scanned} items from {self.table_name}, '
                f'returned {total_count} items after filtering'
            )

            result = {
                'Items': all_items,
                'Count': total_count,
                'ScannedCount': total_scanned,
            }

            if last_evaluated_key:
                result['LastEvaluatedKey'] = last_evaluated_key

            return result

        except Exception as e:
            logging.error(f'Error querying {self.table_name}: {str(e)}')
            raise

    def _query_generator(self, query_params, max_items):
        """
        Generator for querying items one at a time.

        Args:
            query_params (dict): Parameters for the query operation.
            max_items (int, optional): Maximum number of items to yield.

        Yields:
            Deserialized items from the query.
        """
        items_yielded = 0
        last_evaluated_key = None

        try:
            while True:
                if last_evaluated_key:
                    query_params['ExclusiveStartKey'] = last_evaluated_key

                response = self.client.query(**query_params)

                for item in response.get('Items', []):
                    yield self._deserialize_item(item)
                    items_yielded += 1

                    if max_items and items_yielded >= max_items:
                        return

                last_evaluated_key = response.get('LastEvaluatedKey')
                if not last_evaluated_key:
                    break

        except Exception as e:
            logging.error(
                f'Error in query generator for {self.table_name}: {str(e)}'
            )
            raise
