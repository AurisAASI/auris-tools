import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from dotenv import load_dotenv

from auris_tools.geminiHandler import GoogleGeminiHandler

# Load environment variables from .env file
load_dotenv()


class TestGoogleGeminiHandler:
    """Tests for the GoogleGeminiHandler class."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test configuration."""
        # Use actual API key from environment
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.test_model = 'gemini-2.0-flash-lite'

        # Skip tests if no API key is available
        if not self.api_key:
            pytest.skip('GEMINI_API_KEY not found in environment variables')

    def test_init_with_api_key(self):
        """Test initialization with provided API key."""
        handler = GoogleGeminiHandler(
            api_key=self.api_key, model=self.test_model
        )

        # Verify handler attributes
        assert handler.api_key == self.api_key
        assert handler.model_name == self.test_model
        assert handler.temperature == 0.5  # default value
        assert (
            handler.response_mime_type == 'application/json'
        )  # default value
        assert handler.model is not None

    def test_init_with_env_api_key(self):
        """Test initialization with API key from environment."""
        handler = GoogleGeminiHandler(model=self.test_model)

        # Verify handler uses environment API key
        assert handler.api_key == self.api_key
        assert handler.model_name == self.test_model

    def test_init_with_custom_parameters(self):
        """Test initialization with custom parameters."""
        custom_temp = 0.8
        custom_mime_type = 'application/xml'

        handler = GoogleGeminiHandler(
            api_key=self.api_key,
            temperature=custom_temp,
            response_mime_type=custom_mime_type,
            model=self.test_model,
        )

        assert handler.temperature == custom_temp
        assert handler.response_mime_type == custom_mime_type
        assert handler.model is not None

    def test_check_model_availability_valid_model(self):
        """Test model availability check with valid model."""
        # This should not raise an exception
        handler = GoogleGeminiHandler(
            api_key=self.api_key, model=self.test_model
        )
        assert handler.model is not None

    def test_check_model_availability_invalid_model(self):
        """Test model availability check with invalid model."""
        with pytest.raises(TypeError) as exc_info:
            GoogleGeminiHandler(
                api_key=self.api_key, model='invalid-model-name-123'
            )

        assert 'Invalid model name: invalid-model-name-123' in str(
            exc_info.value
        )

    def test_generate_output_success(self):
        """Test successful content generation with real API."""
        handler = GoogleGeminiHandler(
            api_key=self.api_key, model=self.test_model
        )

        test_prompt = "Say 'Hello World' and nothing else."
        result = handler.generate_output(test_prompt)

        # Verify we got a response
        assert result is not None
        assert result != ''

        # Check that response has expected structure
        assert hasattr(result, 'text') or hasattr(result, 'candidates')

    @patch('auris_tools.geminiHandler.logger')
    def test_generate_output_with_api_error(self, mock_logger):
        """Test content generation handles API errors gracefully."""
        # Create handler with valid API key first
        handler = GoogleGeminiHandler(
            api_key=self.api_key, model=self.test_model
        )

        # Mock the model's generate_content method to raise an exception
        with patch.object(
            handler.model,
            'generate_content',
            side_effect=Exception('API Error'),
        ):
            result = handler.generate_output('Test prompt')

            # Should return empty string on error
            assert result == ''

    def test_get_text_success(self):
        """Test successful text extraction from response."""
        handler = GoogleGeminiHandler(
            api_key=self.api_key, model=self.test_model
        )

        mock_response = {
            'candidates': [{'content': 'This is the generated text'}]
        }

        result = handler.get_text(mock_response)
        assert result == 'This is the generated text'

    @patch('auris_tools.geminiHandler.logger')
    def test_get_text_no_candidates(self, mock_logger):
        """Test text extraction with no candidates."""
        handler = GoogleGeminiHandler(
            api_key=self.api_key, model=self.test_model
        )

        mock_response = {'candidates': []}

        result = handler.get_text(mock_response)

        mock_logger.warning.assert_called_once()
        assert 'No candidates found in the response' in str(
            mock_logger.warning.call_args
        )
        assert result == ''

    def test_real_integration_flow(self):
        """Test a complete integration flow with real API calls."""
        handler = GoogleGeminiHandler(
            api_key=self.api_key, model=self.test_model
        )

        # Generate content
        prompt = 'What is 2+2? Answer with just the number.'
        response = handler.generate_output(prompt)

        # Verify response is valid
        assert response is not None
        assert response != ''

        # Test with different mime type
        handler_text = GoogleGeminiHandler(
            api_key=self.api_key,
            model=self.test_model,
            response_mime_type='text/plain',
        )

        text_response = handler_text.generate_output('Say hello in one word.')
        assert text_response is not None

    def test_default_model_fallback(self):
        """Test that default model is used when none specified."""
        handler = GoogleGeminiHandler(api_key=self.api_key)

        # Should use default model
        assert handler.model_name == 'gemini-2.5-flash'
        assert handler.model is not None
