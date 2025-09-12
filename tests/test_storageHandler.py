import os

import pytest

from auris_tools.configuration import AWSConfiguration
from auris_tools.storageHandler import StorageHandler

DATA_SAMPLES_PATH = os.path.join(os.path.dirname(__file__), 'data')
TEST_BUCKET_NAME = 'auris-code-tests'


def test_init_with_default_config():
    """Test initialization with default configuration."""
    # Execute
    handler = StorageHandler()

    # Assert
    assert handler.client is not None
    assert handler.client.__class__.__name__ == 'S3'


def test_init_with_custom_config():
    """Test initialization with custom configuration."""
    # Setup custom config
    custom_config = AWSConfiguration()
    custom_config.region = 'us-east-1'  # Using a different region

    # Execute
    handler = StorageHandler(config=custom_config)

    # Assert
    assert handler.client is not None
    assert handler.client.__class__.__name__ == 'S3'
    assert handler.client.meta.region_name == 'us-east-1'


def test_init_with_test_data_access():
    """Test that the client can access test data."""
    # Setup
    assert os.path.exists(DATA_SAMPLES_PATH), 'Test data directory not found'

    # Execute
    handler = StorageHandler()

    # Check if we can access a specific test file
    test_file_key = 'plain_text_sample.txt'
    response = handler.client.get_object(
        Bucket=TEST_BUCKET_NAME, Key=test_file_key
    )
    assert response is not None


def test_upload_file_success():
    """Test successful file upload."""
    # Setup
    handler = StorageHandler()
    test_file = os.path.join(DATA_SAMPLES_PATH, 'plain_text_sample.txt')

    # Execute
    result = handler.upload_file(
        test_file, TEST_BUCKET_NAME, 'plain_text_sample.txt'
    )

    assert result is True


def test_upload_file_failure():
    """Test file upload failure with non-existent file."""
    # Setup
    handler = StorageHandler()
    non_existent_file = os.path.join(DATA_SAMPLES_PATH, 'non_existent.txt')

    # Execute
    result = handler.upload_file(
        non_existent_file, TEST_BUCKET_NAME, 'non_existent.txt'
    )

    assert result is False


def test_download_file_success(tmpdir):
    """Test successful file download."""
    # Setup
    handler = StorageHandler()
    download_path = os.path.join(tmpdir, 'plain_text_sample.txt')

    # Execute
    result = handler.download_file(
        TEST_BUCKET_NAME, 'plain_text_sample.txt', download_path
    )

    assert result is True
    assert os.path.exists(download_path)

    # Clean up
    os.remove(download_path)


def test_download_file_failure():
    """Test file download failure with non-existent file."""
    # Setup
    handler = StorageHandler()
    non_existent_file = os.path.join(DATA_SAMPLES_PATH, 'non_existent.txt')

    # Execute
    result = handler.download_file(
        TEST_BUCKET_NAME, 'non_existent.txt', non_existent_file
    )

    assert result is False


def test_check_file_exists_success():
    """Test checking if a file exists."""
    # Setup
    handler = StorageHandler()

    # Execute
    exists = handler.check_file_exists(
        TEST_BUCKET_NAME, 'plain_text_sample.txt'
    )

    assert exists is True


def test_check_file_size_success():
    """Test checking the size of a file."""
    # Setup
    handler = StorageHandler()

    # Execute
    size = handler.check_file_size(TEST_BUCKET_NAME, 'plain_text_sample.txt')

    assert size is not None
    assert size > 0


def test_check_file_size_failure():
    """Test file check file size failure with non-existent file."""
    # Setup
    handler = StorageHandler()
    non_existent_file = os.path.join(DATA_SAMPLES_PATH, 'non_existent.txt')

    # Execute
    result = handler.check_file_size(TEST_BUCKET_NAME, 'non_existent.txt')

    assert result is None


def test_delete_file_success(tmpdir):
    """Test successful file deletion."""
    # Setup
    handler = StorageHandler()

    # First, upload a file to ensure it exists
    test_file = os.path.join(DATA_SAMPLES_PATH, 'plain_text_sample.txt')
    # Copy the file to tmpdir first
    tmp_file = os.path.join(tmpdir, 'file_to_delete.txt')
    with open(test_file, 'rb') as src, open(tmp_file, 'wb') as dst:
        dst.write(src.read())
    # test_file = tmp_file
    handler.upload_file(tmp_file, TEST_BUCKET_NAME, 'file_to_delete.txt')

    # Execute
    result = handler.delete_file(TEST_BUCKET_NAME, 'file_to_delete.txt')

    assert result is True

    # Verify deletion
    exists = handler.check_file_exists(TEST_BUCKET_NAME, 'file_to_delete.txt')
    assert exists is False


def test_delete_file_failure():
    """Test file deletion failure with non-existent file."""
    # Setup
    handler = StorageHandler()

    # Execute
    result = handler.delete_file(TEST_BUCKET_NAME, 'non_existent.txt')

    assert result is False


def test_list_files_success():
    """Test listing files in a bucket."""
    # Setup
    handler = StorageHandler()

    # Execute
    files = handler.list_files(TEST_BUCKET_NAME)

    assert isinstance(files, list)
    assert len(files) > 0


def test_get_file_object_success():
    """Test getting a file object."""
    # Setup
    handler = StorageHandler()

    # Execute
    obj = handler.get_file_object(TEST_BUCKET_NAME, 'plain_text_sample.txt')

    assert obj is not None

    # Test getting using as_byte option
    obj_byte = handler.get_file_object(
        TEST_BUCKET_NAME, 'plain_text_sample.txt', as_bytes=True
    )
    assert obj_byte is not None
    assert isinstance(obj_byte, bytes)
    assert len(obj_byte) > 0
