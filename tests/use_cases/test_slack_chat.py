from unittest.mock import mock_open, patch

import pytest

from app.interfaces.conversation_repository import DuplicateMessageError
from app.use_cases.slack_chat import HandleMessageError, SlackService


class TestSlackService:
    """
    Tests for the SlackService class.
    """

    @patch("builtins.open", new_callable=mock_open, read_data='{"system": "You are a helpful assistant."}')
    @patch("os.path.exists", return_value=True)
    def test_init_with_initial_context(self, mock_exists, mock_file, mock_conversation_repo, mock_llm_chat):
        """
        Test initialization with initial context.
        """
        # Act
        service = SlackService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
        )

        # Assert
        assert hasattr(service, "initial_context")
        assert service.initial_context == {"system": "You are a helpful assistant."}
        mock_exists.assert_called_once()
        mock_file.assert_called_once()

    @patch("os.path.exists", return_value=False)
    def test_init_without_initial_context(self, mock_exists, mock_conversation_repo, mock_llm_chat):
        """
        Test initialization without initial context.
        """
        # Act
        service = SlackService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
        )

        # Assert
        assert not hasattr(service, "initial_context")
        mock_exists.assert_called_once()

    def test_initialize_conversation(self, mock_conversation_repo, mock_llm_chat):
        """
        Test the initialize_conversation method.
        """
        # Arrange
        service = SlackService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
        )
        service.initial_context = {"system": "You are a helpful assistant."}

        # Act
        service.initialize_conversation("slack-C12345")

        # Assert
        mock_conversation_repo.initialize_conversation.assert_called_once_with(
            conversation_id="slack-C12345", initial_context={"system": "You are a helpful assistant."}
        )

    def test_handle_message_success(self, mock_conversation_repo, mock_llm_chat, sample_slack_event, mock_web_client):
        """
        Test the handle_message method with a successful execution.
        """
        # Arrange
        service = SlackService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
        )
        service.initial_context = {"system": "You are a helpful assistant."}
        mock_conversation_repo.add_message.return_value = [{"role": "user", "content": "Hello"}]
        mock_llm_chat.send_message.return_value = "Hello! How can I help you today?"

        # Act
        service.handle_message(sample_slack_event, mock_web_client)

        # Assert
        mock_conversation_repo.add_message.assert_called()
        mock_llm_chat.start_chat.assert_called_once()
        mock_llm_chat.send_message.assert_called_once_with("Hello, how are you?")
        mock_web_client.chat_postMessage.assert_called_once()
        mock_web_client.chat_update.assert_called_once()

    def test_handle_message_duplicate(self, mock_conversation_repo, mock_llm_chat, sample_slack_event, mock_web_client):
        """
        Test the handle_message method with a duplicate message.
        """
        # Arrange
        service = SlackService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
        )
        service.initial_context = {"system": "You are a helpful assistant."}
        mock_conversation_repo.add_message.side_effect = DuplicateMessageError("Duplicate message")

        # Act
        result = service.handle_message(sample_slack_event, mock_web_client)

        # Assert
        assert result is None
        mock_conversation_repo.add_message.assert_called_once()
        mock_llm_chat.start_chat.assert_not_called()
        mock_llm_chat.send_message.assert_not_called()
        mock_web_client.chat_postMessage.assert_not_called()
        mock_web_client.chat_update.assert_not_called()

    def test_handle_message_error(self, mock_conversation_repo, mock_llm_chat, sample_slack_event, mock_web_client):
        """
        Test the handle_message method with an error.
        """
        # Arrange
        service = SlackService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
        )
        service.initial_context = {"system": "You are a helpful assistant."}
        mock_conversation_repo.add_message.return_value = [{"role": "user", "content": "Hello"}]
        mock_llm_chat.send_message.side_effect = Exception("Test error")

        # Act & Assert
        with pytest.raises(HandleMessageError) as exc_info:
            service.handle_message(sample_slack_event, mock_web_client)

        assert isinstance(exc_info.value.exception, Exception)
        assert str(exc_info.value.exception) == "Test error"
        assert exc_info.value.placeholder_ts == "test_timestamp"
        assert exc_info.value.thread_ts is None
        mock_conversation_repo.add_message.assert_called_once()
        mock_llm_chat.start_chat.assert_called_once()
        mock_llm_chat.send_message.assert_called_once()
        mock_web_client.chat_postMessage.assert_called_once()
        mock_web_client.chat_update.assert_not_called()

    def test_handle_threaded_message(
        self, mock_conversation_repo, mock_llm_chat, sample_slack_threaded_event, mock_web_client
    ):
        """
        Test the handle_message method with a threaded message.
        """
        # Arrange
        service = SlackService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
        )
        service.initial_context = {"system": "You are a helpful assistant."}
        mock_conversation_repo.add_message.return_value = [{"role": "user", "content": "Hello"}]
        mock_llm_chat.send_message.return_value = "Hello! How can I help you today?"

        # Act
        service.handle_message(sample_slack_threaded_event, mock_web_client)

        # Assert
        mock_conversation_repo.add_message.assert_called_once()
        mock_llm_chat.start_chat.assert_called_once()
        mock_llm_chat.send_message.assert_called_once_with("This is a threaded reply")
        mock_web_client.chat_postMessage.assert_called_once_with(
            channel="C12345",
            mrkdwn=True,
            text=":hourglass_flowing_sand: _Thinking..._",
            blocks=service._get_context_block(":hourglass_flowing_sand: _Thinking..._"),
            thread_ts="1609502400.000100",
        )
        mock_web_client.chat_update.assert_called_once()

    def test_get_context_block(self, mock_conversation_repo, mock_llm_chat):
        """
        Test the _get_context_block method.
        """
        # Arrange
        service = SlackService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
        )

        # Act
        result = service._get_context_block("Test message")

        # Assert
        assert result == [
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Test message",
                    }
                ],
            }
        ]

    def test_get_markdown_block(self, mock_conversation_repo, mock_llm_chat):
        """
        Test the _get_markdown_block method.
        """
        # Arrange
        service = SlackService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
        )

        # Act
        result = service._get_markdown_block("Test message")

        # Assert
        assert result == [
            {
                "type": "markdown",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Test message",
                    }
                ],
            }
        ]
