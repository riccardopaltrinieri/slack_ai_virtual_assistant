from unittest.mock import MagicMock, patch

import pytest

from app.integrations.gemini import GeminiChat


@pytest.fixture
def mock_genai():
    """
    Create a mock for the google.generativeai module.
    """
    with patch("app.integrations.gemini.genai") as mock:
        yield mock


@pytest.fixture
def mock_generative_model():
    """
    Create a mock for the GenerativeModel class.
    """
    mock_model = MagicMock()
    mock_chat_session = MagicMock()
    mock_model.start_chat.return_value = mock_chat_session
    mock_chat_session.send_message.return_value.text = "Hello, I'm Gemini!"
    mock_chat_session.history = [
        {"role": "user", "parts": [{"text": "Hello"}]},
        {"role": "model", "parts": [{"text": "Hello, I'm Gemini!"}]},
    ]
    return mock_model


class TestGeminiChat:
    """
    Tests for the GeminiChat class.
    """

    def test_init_with_api_key(self, mock_genai, mock_generative_model):
        """
        Test initialization with an API key.
        """
        # Arrange
        mock_genai.GenerativeModel.return_value = mock_generative_model
        api_key = "test_api_key"

        # Act
        chat = GeminiChat(api_key=api_key)

        # Assert
        mock_genai.configure.assert_called_once_with(api_key=api_key)
        mock_genai.GenerativeModel.assert_called_once()
        assert chat.model == mock_generative_model
        assert chat.chat_session is None

    def test_init_without_api_key(self, mock_genai, mock_generative_model):
        """
        Test initialization without an API key.
        """
        # Arrange
        mock_genai.GenerativeModel.return_value = mock_generative_model

        # Act
        chat = GeminiChat()

        # Assert
        mock_genai.configure.assert_not_called()
        mock_genai.GenerativeModel.assert_called_once()
        assert chat.model == mock_generative_model
        assert chat.chat_session is None

    def test_start_chat_without_messages(self, mock_genai, mock_generative_model):
        """
        Test starting a chat without initial messages.
        """
        # Arrange
        mock_genai.GenerativeModel.return_value = mock_generative_model
        chat = GeminiChat()

        # Act
        chat.start_chat()

        # Assert
        mock_generative_model.start_chat.assert_called_once_with(history=[])
        assert chat.chat_session == mock_generative_model.start_chat.return_value

    def test_start_chat_with_messages(self, mock_genai, mock_generative_model):
        """
        Test starting a chat with initial messages.
        """
        # Arrange
        mock_genai.GenerativeModel.return_value = mock_generative_model
        chat = GeminiChat()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        # Act
        chat.start_chat(messages)

        # Assert
        # System messages should be filtered out
        expected_history = [
            {"role": "user", "parts": [{"text": "Hello"}]},
            {"role": "assistant", "parts": [{"text": "Hi there!"}]},
        ]
        mock_generative_model.start_chat.assert_called_once_with(history=expected_history)
        assert chat.chat_session == mock_generative_model.start_chat.return_value

    def test_convert_history(self):
        """
        Test the _convert_history method.
        """
        # Arrange
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
            {"role": "", "content": "This should be skipped"},
            {"role": "user", "content": ""},
        ]

        # Act
        result = GeminiChat._convert_history(messages)

        # Assert
        expected = [
            {"role": "user", "parts": [{"text": "Hello"}]},
            {"role": "assistant", "parts": [{"text": "Hi there!"}]},
            {"role": "user", "parts": [{"text": "How are you?"}]},
        ]
        assert list(result) == expected

    def test_send_message_without_chat_session(self, mock_genai, mock_generative_model):
        """
        Test sending a message without starting a chat session first.
        """
        # Arrange
        mock_genai.GenerativeModel.return_value = mock_generative_model
        chat = GeminiChat()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            chat.send_message("Hello")
        assert "No chat session has been started" in str(exc_info.value)

    def test_send_message_success(self, mock_genai, mock_generative_model):
        """
        Test sending a message successfully.
        """
        # Arrange
        mock_genai.GenerativeModel.return_value = mock_generative_model
        chat = GeminiChat()
        chat.start_chat()

        # Act
        response = chat.send_message("Hello")

        # Assert
        assert response == "Hello, I'm Gemini!"
        chat.chat_session.send_message.assert_called_once_with("Hello")

    def test_send_message_error(self, mock_genai, mock_generative_model):
        """
        Test sending a message with an error.
        """
        # Arrange
        mock_genai.GenerativeModel.return_value = mock_generative_model
        chat = GeminiChat()
        chat.start_chat()
        chat.chat_session.send_message.side_effect = Exception("API error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            chat.send_message("Hello")
        assert "Error sending message to Gemini Chat API" in str(exc_info.value)
        assert "API error" in str(exc_info.value)

    def test_get_history_without_chat_session(self, mock_genai, mock_generative_model):
        """
        Test getting history without starting a chat session first.
        """
        # Arrange
        mock_genai.GenerativeModel.return_value = mock_generative_model
        chat = GeminiChat()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            chat.get_history()
        assert "No chat session has been started" in str(exc_info.value)

    def test_get_history_success(self, mock_genai, mock_generative_model):
        """
        Test getting history successfully.
        """
        # Arrange
        mock_genai.GenerativeModel.return_value = mock_generative_model
        chat = GeminiChat()
        chat.start_chat()

        # Act
        history = chat.get_history()

        # Assert
        expected = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hello, I'm Gemini!"},
        ]
        assert history == expected
