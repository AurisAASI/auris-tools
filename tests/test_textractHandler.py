from unittest.mock import MagicMock, patch

import boto3
import botocore.session
import pytest
from botocore.stub import Stubber

from auris_tools.configuration import AWSConfiguration
from auris_tools.textractHandler import TextractHandler


class TestTextractHandler:
    """Tests for the TextractHandler class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        # Create a base configuration for tests
        self.config = AWSConfiguration(
            access_key='TEST_ACCESS_KEY',
            secret_key='TEST_SECRET_KEY',
            region='us-east-1',
        )
        self.test_bucket = 'test-bucket'
        self.test_document = 'test-document.pdf'
        self.test_job_id = '1234567890abcdef0'

        # Create a mock Textract client
        self.mock_client = MagicMock()
        self.patcher = patch('boto3.session.Session')
        self.mock_session = self.patcher.start()
        self.mock_session.return_value.client.return_value = self.mock_client

        # Create the handler with mocked dependencies
        self.textract_handler = TextractHandler(config=self.config)

        yield
        self.patcher.stop()

    def test_init_with_parameters(self):
        """Test initialization with parameters."""
        # This is testing that the client was correctly initialized from the setup
        assert isinstance(self.textract_handler, TextractHandler)
        assert self.textract_handler.client is not None
        self.mock_session.assert_called_once()
        self.mock_session.return_value.client.assert_called_with(
            'textract', **self.config.get_client_args()
        )

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        with patch(
            'auris_tools.textractHandler.AWSConfiguration'
        ) as mock_config:
            mock_config.return_value = self.config
            handler = TextractHandler()
            assert handler.client is not None
            mock_config.assert_called_once()

    def test_start_job(self):
        """Test starting a Textract job."""
        # Setup the mock to return a job ID
        self.mock_client.start_document_text_detection.return_value = {
            'JobId': self.test_job_id
        }

        # Call the method
        job_id = self.textract_handler.start_job(
            self.test_bucket, self.test_document
        )

        # Assert the result and that the client was called correctly
        assert job_id == self.test_job_id
        self.mock_client.start_document_text_detection.assert_called_once_with(
            DocumentLocation={
                'S3Object': {
                    'Bucket': self.test_bucket,
                    'Name': self.test_document,
                }
            }
        )

    def test_start_job_error(self):
        """Test error handling when starting a job."""
        # Setup the mock to raise an exception
        self.mock_client.start_document_text_detection.side_effect = Exception(
            'Test error'
        )

        # Call the method and check it raises the exception
        with pytest.raises(Exception, match='Test error'):
            self.textract_handler.start_job(
                self.test_bucket, self.test_document
            )

    def test_get_job_status(self):
        """Test getting job status."""
        # Setup the mock to return a status
        self.mock_client.get_document_text_detection.return_value = {
            'JobStatus': 'SUCCEEDED'
        }

        # Call the method
        status = self.textract_handler.get_job_status(self.test_job_id)

        # Assert the result and that the client was called correctly
        assert status == 'SUCCEEDED'
        self.mock_client.get_document_text_detection.assert_called_once_with(
            JobId=self.test_job_id
        )

    def test_get_job_status_error(self):
        """Test error handling when getting job status."""
        # Setup the mock to raise an exception
        self.mock_client.get_document_text_detection.side_effect = Exception(
            'Test error'
        )

        # Call the method and check it raises the exception
        with pytest.raises(Exception, match='Test error'):
            self.textract_handler.get_job_status(self.test_job_id)

    def test_is_job_complete(self):
        """Test checking if a job is complete."""
        # Setup the mock to return a status
        self.mock_client.get_document_text_detection.return_value = {
            'JobStatus': 'SUCCEEDED'
        }

        # Call the method with mocked time.sleep
        with patch('time.sleep') as mock_sleep:
            status = self.textract_handler.is_job_complete(self.test_job_id)

            # Assert the result and that time.sleep was called
            assert status == 'SUCCEEDED'
            mock_sleep.assert_called_once_with(1)

    def test_get_job_results_single_page(self):
        """Test getting job results with a single page."""
        # Setup the mock to return a single page of results
        self.mock_client.get_document_text_detection.return_value = {
            'JobStatus': 'SUCCEEDED',
            'Blocks': [{'BlockType': 'LINE', 'Text': 'Test text'}],
        }

        # Call the method
        results = self.textract_handler.get_job_results(self.test_job_id)

        # Assert the results and that the client was called correctly
        assert len(results) == 1
        assert results[0]['JobStatus'] == 'SUCCEEDED'
        self.mock_client.get_document_text_detection.assert_called_once_with(
            JobId=self.test_job_id
        )

    def test_get_job_results_multiple_pages(self):
        """Test getting job results with multiple pages."""
        # Setup the mock to return multiple pages of results
        self.mock_client.get_document_text_detection.side_effect = [
            {
                'JobStatus': 'SUCCEEDED',
                'Blocks': [{'BlockType': 'LINE', 'Text': 'Page 1'}],
                'NextToken': 'token1',
            },
            {
                'JobStatus': 'SUCCEEDED',
                'Blocks': [{'BlockType': 'LINE', 'Text': 'Page 2'}],
                'NextToken': 'token2',
            },
            {
                'JobStatus': 'SUCCEEDED',
                'Blocks': [{'BlockType': 'LINE', 'Text': 'Page 3'}],
            },
        ]

        # Call the method with mocked time.sleep
        with patch('time.sleep') as mock_sleep:
            results = self.textract_handler.get_job_results(self.test_job_id)

            # Assert the results and that the client was called correctly
            assert len(results) == 3
            assert results[0]['Blocks'][0]['Text'] == 'Page 1'
            assert results[1]['Blocks'][0]['Text'] == 'Page 2'
            assert results[2]['Blocks'][0]['Text'] == 'Page 3'

            # Check pagination was handled correctly
            assert self.mock_client.get_document_text_detection.call_count == 3
            self.mock_client.get_document_text_detection.assert_any_call(
                JobId=self.test_job_id
            )
            self.mock_client.get_document_text_detection.assert_any_call(
                JobId=self.test_job_id, NextToken='token1'
            )
            self.mock_client.get_document_text_detection.assert_any_call(
                JobId=self.test_job_id, NextToken='token2'
            )

            # Check sleep was called between pagination requests
            assert mock_sleep.call_count == 2

    def test_get_full_text(self):
        """Test extracting full text from Textract response."""
        # Create a mock response with text blocks
        mock_response = [
            {
                'Blocks': [
                    {'BlockType': 'PAGE', 'Text': None},
                    {'BlockType': 'LINE', 'Text': 'This is line 1.'},
                    {'BlockType': 'WORD', 'Text': 'This'},
                    {'BlockType': 'LINE', 'Text': 'This is line 2.'},
                ]
            },
            {
                'Blocks': [
                    {'BlockType': 'PAGE', 'Text': None},
                    {'BlockType': 'LINE', 'Text': 'This is line 3.'},
                    {'BlockType': 'WORD', 'Text': 'line'},
                    {'BlockType': 'LINE', 'Text': 'This is line 4.'},
                ]
            },
        ]

        # Call the method
        text = self.textract_handler.get_full_text(mock_response)

        # Assert the text was extracted correctly
        expected_text = (
            'This is line 1. This is line 2. This is line 3. This is line 4.'
        )
        assert text == expected_text

    def test_get_full_text_empty_response(self):
        """Test handling empty response when extracting text."""
        # Call the method with an empty response
        text = self.textract_handler.get_full_text([{'Blocks': []}])

        # Assert the result is an empty string
        assert text == ''

    def test_get_full_text_error(self):
        """Test error handling when extracting text."""
        # Call the method with invalid input
        text = self.textract_handler.get_full_text('invalid')

        # Assert the result is an empty string
        assert text == ''
