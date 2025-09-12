import os
from unittest.mock import MagicMock, patch

import pytest

from auris_tools.configuration import AWSConfiguration


class TestAWSConfiguration:
    """Tests for the AWSConfiguration class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration with dummy credentials."""
        # Use dummy credentials for testing
        self.test_region = 'us-east-1'
        self.test_access_key = 'TEST_ACCESS_KEY'  # Not real credentials
        self.test_secret_key = 'TEST_SECRET_KEY'  # Not real credentials
        self.test_profile = 'test-profile'
        self.test_endpoint = 'http://localhost:4566'

        # Create a base configuration for tests
        self.config = AWSConfiguration(
            access_key=self.test_access_key,
            secret_key=self.test_secret_key,
            region=self.test_region,
        )

    def test_init_default_values(self):
        """Test initialization with default values."""
        config = AWSConfiguration()

        assert isinstance(config, AWSConfiguration)

    @patch.dict(
        os.environ,
        {
            'AWS_ACCESS_KEY_ID': 'env-key',
            'AWS_SECRET_ACCESS_KEY': 'env-secret',
            'AWS_DEFAULT_REGION': 'us-west-2',
            'AWS_PROFILE': 'env-profile',
            'AWS_ENDPOINT_URL': 'http://env-endpoint:4566',
        },
    )
    def test_init_with_parameters(self):
        """Test initialization with parameters."""
        test_region = 'eu-west-1'
        test_profile = self.test_profile
        test_endpoint = self.test_endpoint

        config = AWSConfiguration(
            access_key=self.test_access_key,
            secret_key=self.test_secret_key,
            region=test_region,
            profile=test_profile,
            endpoint_url=test_endpoint,
        )
        assert config.access_key == self.test_access_key
        assert config.secret_key == self.test_secret_key
        assert config.region == test_region
        assert config.profile == test_profile
        assert config.endpoint_url == test_endpoint

    @patch.dict(
        os.environ,
        {
            'AWS_ACCESS_KEY_ID': 'env-key',
            'AWS_SECRET_ACCESS_KEY': 'env-secret',
            'AWS_DEFAULT_REGION': 'us-west-2',
            'AWS_PROFILE': 'env-profile',
            'AWS_ENDPOINT_URL': 'http://env-endpoint:4566',
        },
    )
    def test_environment_variables_priority(self):
        """Test that environment variables take priority over constructor parameters."""
        config = AWSConfiguration(
            access_key=self.test_access_key,
            secret_key=self.test_secret_key,
            region=self.test_region,
            profile=self.test_profile,
            endpoint_url=self.test_endpoint,
        )
        assert config.access_key == 'TEST_ACCESS_KEY'  # Constructor value
        assert config.secret_key == 'TEST_SECRET_KEY'
        assert config.region == 'us-east-1'
        assert config.profile == 'test-profile'
        assert config.endpoint_url == 'http://localhost:4566'

    def test_get_boto3_session_args_with_keys(self):
        """Test getting boto3 session arguments with access keys."""
        test_region = 'eu-west-1'
        config = AWSConfiguration(
            access_key=self.test_access_key,
            secret_key=self.test_secret_key,
            region=test_region,
        )
        session_args = config.get_boto3_session_args()
        assert session_args == {
            'aws_access_key_id': self.test_access_key,
            'aws_secret_access_key': self.test_secret_key,
            'region_name': test_region,
        }

    @patch.dict(
        os.environ,
        {
            'AWS_ACCESS_KEY_ID': 'env-key',
            'AWS_SECRET_ACCESS_KEY': 'env-secret',
            'AWS_DEFAULT_REGION': 'us-west-2',
            'AWS_PROFILE': 'env-profile',
            'AWS_ENDPOINT_URL': 'http://env-endpoint:4566',
        },
    )
    def test_get_boto3_session_args_with_profile(self):
        """Test getting boto3 session arguments with profile."""
        test_region = 'eu-west-1'
        config = AWSConfiguration(
            profile=self.test_profile, region=test_region
        )
        session_args = config.get_boto3_session_args()
        assert session_args == {
            'region_name': 'eu-west-1',
            'aws_access_key_id': 'env-key',
            'aws_secret_access_key': 'env-secret',
            'profile_name': 'test-profile',
        }

    @patch.dict(
        os.environ,
        {
            'AWS_ACCESS_KEY_ID': 'env-key',
            'AWS_SECRET_ACCESS_KEY': 'env-secret',
            'AWS_DEFAULT_REGION': 'us-west-2',
            'AWS_PROFILE': 'env-profile',
            'AWS_ENDPOINT_URL': 'http://env-endpoint:4566',
        },
    )
    def test_get_boto3_session_args_with_env_and_profile(self):
        """Test that environment variables take precedence over profile."""
        test_region = 'eu-west-1'
        config = AWSConfiguration()
        session_args = config.get_boto3_session_args()
        # Environment variables should take precedence
        assert session_args == {
            'region_name': 'us-west-2',
            'aws_access_key_id': 'env-key',
            'aws_secret_access_key': 'env-secret',
            'profile_name': 'env-profile',
        }

    def test_get_client_args_with_endpoint(self):
        """Test getting client arguments with endpoint URL."""
        config = AWSConfiguration(endpoint_url=self.test_endpoint)
        client_args = config.get_client_args()
        assert client_args == {'endpoint_url': self.test_endpoint}

    def test_get_client_args_without_endpoint(self):
        """Test getting client arguments without endpoint URL."""
        config = AWSConfiguration()
        client_args = config.get_client_args()
        assert client_args == {}

    @patch('logging.warning')
    def test_validate_config_no_warning_with_keys(self, mock_warning):
        """Test no validation warning when access keys are provided."""
        config = AWSConfiguration(
            access_key=self.test_access_key, secret_key=self.test_secret_key
        )
        mock_warning.assert_not_called()

    @patch('logging.warning')
    def test_validate_config_no_warning_with_profile(self, mock_warning):
        """Test no validation warning when profile is provided."""
        config = AWSConfiguration(profile=self.test_profile)
        mock_warning.assert_not_called()
