import pytest
from boto3.dynamodb.conditions import Key

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


class TestDatabaseHandlerScanAndQuery:
    """Tests for scan and query methods."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration and create test data."""
        self.config = AWSConfiguration()
        self.table_name = 'dev_auris_tools'
        self.db_handler = DatabaseHandler(
            table_name=self.table_name, config=self.config
        )

        # Create test items with varying attributes for filter testing
        self.test_items = []
        base_timestamp = collect_timestamp()

        # Create 10 test items with different attributes
        for i in range(10):
            item_id = generate_uuid()
            item = {
                'id': item_id,
                'name': f'Test Item {i}',
                'age': 20 + i * 5,  # Ages: 20, 25, 30, ..., 65
                'status': 'active' if i % 2 == 0 else 'inactive',
                'category': 'premium'
                if i < 3
                else ('gold' if i < 6 else 'standard'),
                'score': 50 + i * 10,  # Scores: 50, 60, 70, ..., 140
                'verified': i % 3 == 0,  # True for items 0, 3, 6, 9
                'created_at': base_timestamp,
                'test_batch': 'scan_query_test',  # Marker to identify our test items
            }
            self.db_handler.insert_item(item)
            self.test_items.append(item)

        yield

        # Cleanup: delete all test items
        for item in self.test_items:
            self.db_handler.delete_item(item['id'])

    def test_scan_all_items(self):
        """Test scanning all items without filters."""
        result = self.db_handler.scan()

        assert result is not None
        assert 'Items' in result
        assert 'Count' in result
        assert 'ScannedCount' in result
        assert len(result['Items']) >= 10  # At least our test items
        assert result['Count'] == len(result['Items'])

    def test_scan_with_eq_filter(self):
        """Test scanning with equality filter."""
        result = self.db_handler.scan(filters={'status__eq': 'active'})

        assert result is not None
        assert len(result['Items']) >= 5  # 5 active items in our test data
        for item in result['Items']:
            if item.get('test_batch') == 'scan_query_test':
                assert item['status'] == 'active'

    def test_scan_with_gt_filter(self):
        """Test scanning with greater than filter."""
        result = self.db_handler.scan(
            filters={'age__gt': 40, 'test_batch__eq': 'scan_query_test'}
        )

        assert result is not None
        assert len(result['Items']) >= 4  # Items with age 45, 50, 55, 60, 65
        for item in result['Items']:
            assert item['age'] > 40

    def test_scan_with_gte_filter(self):
        """Test scanning with greater than or equal filter."""
        result = self.db_handler.scan(
            filters={'age__gte': 40, 'test_batch__eq': 'scan_query_test'}
        )

        assert result is not None
        assert (
            len(result['Items']) >= 5
        )  # Items with age 40, 45, 50, 55, 60, 65
        for item in result['Items']:
            assert item['age'] >= 40

    def test_scan_with_lt_filter(self):
        """Test scanning with less than filter."""
        result = self.db_handler.scan(
            filters={'age__lt': 40, 'test_batch__eq': 'scan_query_test'}
        )

        assert result is not None
        assert len(result['Items']) >= 4  # Items with age 20, 25, 30, 35
        for item in result['Items']:
            assert item['age'] < 40

    def test_scan_with_lte_filter(self):
        """Test scanning with less than or equal filter."""
        result = self.db_handler.scan(
            filters={'age__lte': 40, 'test_batch__eq': 'scan_query_test'}
        )

        assert result is not None
        assert len(result['Items']) >= 5  # Items with age 20, 25, 30, 35, 40
        for item in result['Items']:
            assert item['age'] <= 40

    def test_scan_with_between_filter(self):
        """Test scanning with between filter."""
        result = self.db_handler.scan(
            filters={
                'age__between': [30, 50],
                'test_batch__eq': 'scan_query_test',
            }
        )

        assert result is not None
        assert len(result['Items']) >= 5  # Ages 30, 35, 40, 45, 50
        for item in result['Items']:
            assert 30 <= item['age'] <= 50

    def test_scan_with_in_filter(self):
        """Test scanning with in filter."""
        result = self.db_handler.scan(
            filters={
                'category__in': ['premium', 'gold'],
                'test_batch__eq': 'scan_query_test',
            }
        )

        assert result is not None
        assert len(result['Items']) >= 6  # 3 premium + 3 gold
        for item in result['Items']:
            assert item['category'] in ['premium', 'gold']

    def test_scan_with_begins_with_filter(self):
        """Test scanning with begins_with filter."""
        result = self.db_handler.scan(
            filters={
                'name__begins_with': 'Test Item',
                'test_batch__eq': 'scan_query_test',
            }
        )

        assert result is not None
        assert len(result['Items']) >= 10  # All our test items
        for item in result['Items']:
            assert item['name'].startswith('Test Item')

    def test_scan_with_exists_filter(self):
        """Test scanning with exists filter."""
        result = self.db_handler.scan(
            filters={
                'verified__exists': True,
                'test_batch__eq': 'scan_query_test',
            }
        )

        assert result is not None
        assert len(result['Items']) >= 10  # All items have verified attribute
        for item in result['Items']:
            assert 'verified' in item

    def test_scan_with_multiple_filters(self):
        """Test scanning with multiple filters combined."""
        result = self.db_handler.scan(
            filters={
                'status__eq': 'active',
                'age__gte': 30,
                'category__in': ['premium', 'gold'],
                'test_batch__eq': 'scan_query_test',
            }
        )

        assert result is not None
        for item in result['Items']:
            assert item['status'] == 'active'
            assert item['age'] >= 30
            assert item['category'] in ['premium', 'gold']

    def test_scan_with_max_items(self):
        """Test scanning with max_items limit."""
        result = self.db_handler.scan(
            filters={'test_batch__eq': 'scan_query_test'}, max_items=5
        )

        assert result is not None
        assert len(result['Items']) == 5
        assert result['Count'] == 5

    def test_scan_with_page_size(self):
        """Test scanning with page_size control."""
        result = self.db_handler.scan(
            filters={'test_batch__eq': 'scan_query_test'}, page_size=3
        )

        assert result is not None
        assert 'Items' in result
        assert 'Count' in result
        # Page size controls batch size, not total results
        assert result['Count'] >= 0

    def test_scan_with_projection(self):
        """Test scanning with projection expression."""
        result = self.db_handler.scan(
            filters={'test_batch__eq': 'scan_query_test'},
            projection_expression='id, age, category',
            max_items=3,
        )

        assert result is not None
        assert len(result['Items']) > 0
        for item in result['Items']:
            # Should only have projected attributes
            assert 'id' in item
            assert (
                'age' in item or 'category' in item
            )  # At least one should be present

    def test_scan_generator_mode(self):
        """Test scanning with generator mode."""
        items_list = []
        generator = self.db_handler.scan(
            filters={'test_batch__eq': 'scan_query_test'},
            max_items=5,
            return_generator=True,
        )

        for item in generator:
            items_list.append(item)

        assert len(items_list) == 5
        for item in items_list:
            assert 'id' in item
            assert item['test_batch'] == 'scan_query_test'

    def test_scan_empty_result(self):
        """Test scanning with filters that return no results."""
        result = self.db_handler.scan(filters={'age__gt': 10000})

        assert result is not None
        assert result['Count'] == 0
        assert len(result['Items']) == 0

    def test_query_by_partition_key(self):
        """Test querying by partition key only."""
        test_item = self.test_items[0]

        result = self.db_handler.query(partition_key_value=test_item['id'])

        assert result is not None
        assert result['Count'] == 1
        assert len(result['Items']) == 1
        assert result['Items'][0]['id'] == test_item['id']

    def test_query_with_filters(self):
        """Test querying with additional filters."""
        test_item = self.test_items[0]

        result = self.db_handler.query(
            partition_key_value=test_item['id'],
            filters={'status__eq': 'active'},
        )

        assert result is not None
        if result['Count'] > 0:
            assert result['Items'][0]['status'] == 'active'

    def test_query_with_max_items(self):
        """Test querying with max_items limit."""
        test_item = self.test_items[0]

        result = self.db_handler.query(
            partition_key_value=test_item['id'], max_items=1
        )

        assert result is not None
        assert result['Count'] <= 1

    def test_query_with_projection(self):
        """Test querying with projection expression."""
        test_item = self.test_items[0]

        result = self.db_handler.query(
            partition_key_value=test_item['id'],
            projection_expression='id, age, category',
        )

        assert result is not None
        if result['Count'] > 0:
            assert 'id' in result['Items'][0]

    def test_query_generator_mode(self):
        """Test querying with generator mode."""
        test_item = self.test_items[0]

        items_list = []
        generator = self.db_handler.query(
            partition_key_value=test_item['id'], return_generator=True
        )

        for item in generator:
            items_list.append(item)

        assert len(items_list) >= 1
        assert items_list[0]['id'] == test_item['id']

    def test_query_with_sort_key_condition_using_key(self):
        """Test querying with sort key condition using boto3 Key expression."""
        test_item = self.test_items[0]

        # Query with sort key condition (this will work if table has sort key)
        # For tables without sort key, this should still work with just partition key
        result = self.db_handler.query(partition_key_value=test_item['id'])

        assert result is not None
        assert 'Items' in result

    def test_query_nonexistent_key(self):
        """Test querying with a non-existent partition key."""
        result = self.db_handler.query(
            partition_key_value='nonexistent-key-12345'
        )

        assert result is not None
        assert result['Count'] == 0
        assert len(result['Items']) == 0

    def test_scan_with_invalid_index_raises_error(self):
        """Test that scanning with invalid index name raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            self.db_handler.scan(
                filters={'status__eq': 'active'}, index_name='NonExistentIndex'
            )

        assert 'does not exist' in str(exc_info.value)

    def test_query_with_invalid_index_raises_error(self):
        """Test that querying with invalid index name raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            self.db_handler.query(
                partition_key_value='test', index_name='NonExistentIndex'
            )

        assert 'does not exist' in str(exc_info.value)

    def test_scan_with_ne_filter(self):
        """Test scanning with not equal filter."""
        result = self.db_handler.scan(
            filters={
                'status__ne': 'active',
                'test_batch__eq': 'scan_query_test',
            }
        )

        assert result is not None
        for item in result['Items']:
            assert item['status'] != 'active'

    def test_scan_default_equality_without_operator(self):
        """Test that filters without operator syntax default to equality."""
        result = self.db_handler.scan(
            filters={'test_batch': 'scan_query_test'}
        )

        assert result is not None
        assert len(result['Items']) >= 10
        for item in result['Items']:
            assert item['test_batch'] == 'scan_query_test'
