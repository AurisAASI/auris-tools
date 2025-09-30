import logging

import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

from auris_tools.configuration import AWSConfiguration
from auris_tools.utils import generate_uuid


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
