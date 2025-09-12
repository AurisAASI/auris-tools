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
        response = self.db_handler.insert_item(self.table_name, item)
        assert response is not None

        # delete the item after test
        self.db_handler.delete_item(self.table_name, item_id)
        # TODO TERMINAR AQUI!!!

    def test_input_item_raise_error_on_invalid_item(self):
        """Test inserting an invalid item raises an error."""
        with pytest.raises(TypeError):
            self.db_handler.insert_item(self.table_name, 'invalid_item')

    def test_get_item_dynamo_notation_success(self):
        """Test retrieving an item successfully."""
        key = {'id': {'S': ID_SAMPLE}}
        item = self.db_handler.get_item(self.table_name, key)
        assert item is not None

    def test_get_item_json_notation_success(self):
        """Test retrieving an item successfully."""
        key = {'id': ID_SAMPLE}
        item = self.db_handler.get_item(self.table_name, key)
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
        self.db_handler.insert_item(self.table_name, temp_item)

        # Verify the item exists
        key = {'id': item_id}
        item = self.db_handler.get_item(self.table_name, key)
        assert item is not None

        # Now delete the item
        result = self.db_handler.delete_item(self.table_name, key)
        assert result is True
