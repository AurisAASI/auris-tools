import pytest

from auris_tools.configuration import AWSConfiguration
from auris_tools.databaseHandlers import DatabaseHandler
from auris_tools.utils import collect_timestamp, generate_uuid

ID_SAMPLE = '6be18162-d20d-4493-91c6-42d20d491a7a'


class TestDatabaseHandler:
    """Tests for the DatabaseHandler class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        # Create a base configuration for tests
        self.config = AWSConfiguration()
        self.table_name = 'dev_auris_tools'
        self.db_handler = DatabaseHandler(
            table_name=self.table_name, config=self.config
        )

    def test_init_invalid_table_name_raise_error(self):
        """Test initialization with invalid table name raises an error."""
        with pytest.raises(Exception) as error:
            DatabaseHandler(
                table_name='invalid_table_name_that_does_not_exist',
                config=self.config,
            )

        assert 'Table does not exist' in str(error.value)

    def test_init_with_parameters(self):
        """Test initialization with parameters."""

        db_handler = DatabaseHandler(table_name=self.table_name)
        assert isinstance(db_handler, DatabaseHandler)
        assert db_handler.table_name == self.table_name

    def test_input_item_success(self):
        """Test inserting an item successfully."""
        item_id = generate_uuid()
        item = {
            'id': item_id,
            'name': 'Test Item',
            'value': 123,
            'is_active': True,
            'tags': ['tag1', 'tag2'],
            'metadata': {'created_by': 'user123'},
            'created_at': collect_timestamp(),
        }
        response = self.db_handler.insert_item(item)
        assert response is not None

        # delete the item after test
        self.db_handler.delete_item(item_id)
        # TODO TERMINAR AQUI!!!

    def test_input_item_raise_error_on_invalid_item(self):
        """Test inserting an invalid item raises an error."""
        with pytest.raises(TypeError):
            self.db_handler.insert_item('invalid_item')

    def test_get_item_dynamo_notation_success(self):
        """Test retrieving an item successfully."""
        key = {'id': {'S': ID_SAMPLE}}
        item = self.db_handler.get_item(key)
        assert item is not None

    def test_get_item_json_notation_success(self):
        """Test retrieving an item successfully."""
        key = {'id': ID_SAMPLE}
        item = self.db_handler.get_item(key)
        assert item is not None

    def test_item_is_serialized(self):
        """Test that an item is correctly serialized for DynamoDB."""
        item = {
            'name': 'Test Item',
            'value': 123,
            'is_active': True,
            'tags': ['tag1', 'tag2'],
            'metadata': {'created_by': 'user123'},
            'created_at': collect_timestamp(),
        }
        is_serialized = self.db_handler.item_is_serialized(item)
        assert is_serialized is False

        dynamo_item = self.db_handler._serialize_item(item)
        is_serialized = self.db_handler.item_is_serialized(dynamo_item)
        assert is_serialized is True

        deserialized_item = self.db_handler._deserialize_item(dynamo_item)
        assert deserialized_item == item

    def test_delete_item_success(self):
        """Test deleting an item successfully."""
        # Create temporary item to test deletion
        item_id = generate_uuid()
        temp_item = {
            'id': item_id,
            'name': 'Temporary Item',
            'value': 456,
            'is_active': True,
            'created_at': item_id,
        }

        # Insert the temporary item
        self.db_handler.insert_item(temp_item)

        # Verify the item exists
        key = {'id': item_id}
        item = self.db_handler.get_item(key)
        assert item is not None

        # Now delete the item
        result = self.db_handler.delete_item(key)
        assert result is True

    def test_update_item_success_with_string_key(self):
        """Test updating an item successfully using a string key."""
        # Create a temporary item to update
        item_id = generate_uuid()
        temp_item = {
            'id': item_id,
            'name': 'Original Name',
            'value': 100,
            'is_active': False,
            'created_at': collect_timestamp(),
        }
        self.db_handler.insert_item(temp_item)

        # Update the item
        updates = {
            'name': 'Updated Name',
            'value': 200,
            'is_active': True,
            'new_field': 'new_value',
        }
        updated_item = self.db_handler.update_item(item_id, updates)

        # Verify the updates
        assert updated_item is not None
        assert updated_item['name'] == 'Updated Name'
        assert updated_item['value'] == 200
        assert updated_item['is_active'] is True
        assert updated_item['new_field'] == 'new_value'
        assert updated_item['id'] == item_id

        # Clean up
        self.db_handler.delete_item(item_id)

    def test_update_item_success_with_dict_key(self):
        """Test updating an item successfully using a dictionary key."""
        # Create a temporary item to update
        item_id = generate_uuid()
        temp_item = {
            'id': item_id,
            'name': 'Original Name',
            'value': 100,
            'created_at': collect_timestamp(),
        }
        self.db_handler.insert_item(temp_item)

        # Update the item using dict key
        key = {'id': item_id}
        updates = {'name': 'Updated Name', 'value': 300}
        updated_item = self.db_handler.update_item(key, updates)

        # Verify the updates
        assert updated_item is not None
        assert updated_item['name'] == 'Updated Name'
        assert updated_item['value'] == 300
        assert updated_item['id'] == item_id

        # Clean up
        self.db_handler.delete_item(item_id)

    def test_update_item_add_new_attributes(self):
        """Test adding new attributes to an existing item."""
        # Create a temporary item
        item_id = generate_uuid()
        temp_item = {
            'id': item_id,
            'name': 'Test Item',
            'created_at': collect_timestamp(),
        }
        self.db_handler.insert_item(temp_item)

        # Add new attributes
        updates = {
            'tags': ['tag1', 'tag2', 'tag3'],
            'metadata': {'author': 'user123', 'version': 1},
            'description': 'A new description',
        }
        updated_item = self.db_handler.update_item(item_id, updates)

        # Verify new attributes were added
        assert updated_item is not None
        assert updated_item['tags'] == ['tag1', 'tag2', 'tag3']
        assert updated_item['metadata'] == {'author': 'user123', 'version': 1}
        assert updated_item['description'] == 'A new description'
        assert updated_item['name'] == 'Test Item'

        # Clean up
        self.db_handler.delete_item(item_id)

    def test_update_item_raises_error_on_nonexistent_key(self):
        """Test that updating a non-existent item raises ValueError."""
        non_existent_id = generate_uuid()
        updates = {'name': 'Updated Name'}

        with pytest.raises(ValueError) as error:
            self.db_handler.update_item(non_existent_id, updates)

        assert 'does not exist' in str(error.value)

    def test_update_item_raises_error_on_invalid_key_type(self):
        """Test that invalid key type raises TypeError."""
        updates = {'name': 'Updated Name'}

        with pytest.raises(TypeError) as error:
            self.db_handler.update_item(12345, updates)

        assert 'Key must be a string identifier or a dictionary' in str(
            error.value
        )

    def test_update_item_raises_error_on_invalid_updates_type(self):
        """Test that invalid updates type raises TypeError."""
        item_id = generate_uuid()

        with pytest.raises(TypeError) as error:
            self.db_handler.update_item(item_id, 'invalid_updates')

        assert 'Updates must be a dictionary' in str(error.value)

    def test_update_item_raises_error_on_empty_updates(self):
        """Test that empty updates dictionary raises ValueError."""
        # Create a temporary item
        item_id = generate_uuid()
        temp_item = {
            'id': item_id,
            'name': 'Test Item',
            'created_at': collect_timestamp(),
        }
        self.db_handler.insert_item(temp_item)

        # Try to update with empty dictionary
        with pytest.raises(ValueError) as error:
            self.db_handler.update_item(item_id, {})

        assert 'Updates dictionary cannot be empty' in str(error.value)

        # Clean up
        self.db_handler.delete_item(item_id)

    def test_update_item_ignores_primary_key_update(self):
        """Test that attempting to update the primary key is ignored."""
        # Create a temporary item
        item_id = generate_uuid()
        temp_item = {
            'id': item_id,
            'name': 'Test Item',
            'value': 100,
            'created_at': collect_timestamp(),
        }
        self.db_handler.insert_item(temp_item)

        # Try to update including the primary key (should be ignored)
        new_id = generate_uuid()
        updates = {'id': new_id, 'name': 'Updated Name', 'value': 200}
        updated_item = self.db_handler.update_item(item_id, updates)

        # Verify that id was not changed but other fields were updated
        assert updated_item is not None
        assert updated_item['id'] == item_id  # Original id preserved
        assert updated_item['name'] == 'Updated Name'
        assert updated_item['value'] == 200

        # Clean up
        self.db_handler.delete_item(item_id)

    def test_update_item_with_complex_data_types(self):
        """Test updating an item with complex data types."""
        from decimal import Decimal

        # Create a temporary item
        item_id = generate_uuid()
        temp_item = {
            'id': item_id,
            'name': 'Test Item',
            'created_at': collect_timestamp(),
        }
        self.db_handler.insert_item(temp_item)

        # Update with complex types (note: using Decimal for numeric values)
        updates = {
            'list_field': [1, 2, 3, 'four', Decimal('5.5')],
            'nested_dict': {
                'level1': {'level2': {'level3': 'deep_value'}},
                'numbers': [10, 20, 30],
            },
            'boolean_field': True,
            'decimal_field': Decimal('3.14159'),
            'null_field': None,
        }
        updated_item = self.db_handler.update_item(item_id, updates)

        # Verify complex types were updated correctly
        assert updated_item is not None
        assert updated_item['list_field'] == [1, 2, 3, 'four', Decimal('5.5')]
        assert (
            updated_item['nested_dict']['level1']['level2']['level3']
            == 'deep_value'
        )
        assert updated_item['boolean_field'] is True
        assert updated_item['decimal_field'] == Decimal('3.14159')
        assert updated_item['null_field'] is None

        # Clean up
        self.db_handler.delete_item(item_id)

    def test_update_item_with_serialized_key(self):
        """Test updating an item using a DynamoDB serialized key."""
        # Create a temporary item
        item_id = generate_uuid()
        temp_item = {
            'id': item_id,
            'name': 'Test Item',
            'value': 100,
            'created_at': collect_timestamp(),
        }
        self.db_handler.insert_item(temp_item)

        # Update using serialized key format
        serialized_key = {'id': {'S': item_id}}
        updates = {'name': 'Updated with Serialized Key', 'value': 500}
        updated_item = self.db_handler.update_item(serialized_key, updates)

        # Verify the updates
        assert updated_item is not None
        assert updated_item['name'] == 'Updated with Serialized Key'
        assert updated_item['value'] == 500
        assert updated_item['id'] == item_id

        # Clean up
        self.db_handler.delete_item(item_id)
