from app.use_cases.daily_prompt import DailyPromptService


class TestDailyPromptService:
    """
    Tests for the DailyPromptService class.
    """

    def test_get_all_conversations(self, mock_conversation_repo, mock_llm_chat, mock_slack_client):
        """
        Test the get_all_conversations method.
        """
        # Arrange
        service = DailyPromptService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
            slack_client=mock_slack_client,
        )
        mock_conversation_repo.find_many.return_value = [{"conversation_id": "test"}]

        # Act
        result = service.get_all_conversations()

        # Assert
        assert result == [{"conversation_id": "test"}]
        mock_conversation_repo.find_many.assert_called_once()

    def test_trigger_daily_prompt_success(
        self, mock_conversation_repo, mock_llm_chat, mock_slack_client, sample_conversation
    ):
        """
        Test the trigger_daily_prompt method with a successful execution.
        """
        # Arrange
        service = DailyPromptService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
            slack_client=mock_slack_client,
        )
        mock_conversation_repo.find_many.return_value = [sample_conversation]
        mock_llm_chat.send_message.return_value = "Here's your daily prompt!"

        # Act
        result, status_code = service.trigger_daily_prompt()

        # Assert
        assert status_code == 200
        assert "successfully" in result
        mock_conversation_repo.find_many.assert_called_once()
        mock_llm_chat.start_chat.assert_called_once_with(sample_conversation["messages"])
        mock_llm_chat.send_message.assert_called_once()
        mock_slack_client.send_message.assert_called_once_with(
            message="Here's your daily prompt!",
            channel="C12345",
        )
        mock_conversation_repo.add_message.assert_called_once()

    def test_trigger_daily_prompt_inactive_conversation(self, mock_conversation_repo, mock_llm_chat, mock_slack_client):
        """
        Test the trigger_daily_prompt method with an inactive conversation.
        """
        # Arrange
        service = DailyPromptService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
            slack_client=mock_slack_client,
        )
        inactive_conversation = {"conversation_id": "slack-C12345", "active": False}
        mock_conversation_repo.find_many.return_value = [inactive_conversation]

        # Act
        result, status_code = service.trigger_daily_prompt()

        # Assert
        assert status_code == 200
        assert "successfully" in result
        mock_conversation_repo.find_many.assert_called_once()
        mock_llm_chat.start_chat.assert_not_called()
        mock_llm_chat.send_message.assert_not_called()
        mock_slack_client.send_message.assert_not_called()
        mock_conversation_repo.add_message.assert_not_called()

    def test_trigger_daily_prompt_error(self, mock_conversation_repo, mock_llm_chat, mock_slack_client):
        """
        Test the trigger_daily_prompt method with an error.
        """
        # Arrange
        service = DailyPromptService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
            slack_client=mock_slack_client,
        )
        mock_conversation_repo.find_many.side_effect = Exception("Test error")

        # Act
        result, status_code = service.trigger_daily_prompt()

        # Assert
        assert status_code == 500
        assert "Error" in result
        assert "Test error" in result
        mock_conversation_repo.find_many.assert_called_once()

    def test_generate_daily_prompt_success(
        self, mock_conversation_repo, mock_llm_chat, mock_slack_client, sample_conversation
    ):
        """
        Test the generate_daily_prompt method with a successful execution.
        """
        # Arrange
        service = DailyPromptService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
            slack_client=mock_slack_client,
        )
        mock_llm_chat.send_message.return_value = "Here's your daily prompt!"

        # Act
        result = service.generate_daily_prompt(sample_conversation)

        # Assert
        assert result == "Here's your daily prompt!"
        mock_llm_chat.start_chat.assert_called_once_with(sample_conversation["messages"])
        mock_llm_chat.send_message.assert_called_once()

    def test_generate_daily_prompt_no_messages(self, mock_conversation_repo, mock_llm_chat, mock_slack_client):
        """
        Test the generate_daily_prompt method with no messages in the conversation.
        """
        # Arrange
        service = DailyPromptService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
            slack_client=mock_slack_client,
        )
        conversation = {"conversation_id": "slack-C12345", "messages": []}

        # Act
        result = service.generate_daily_prompt(conversation)

        # Assert
        assert "No messages found" in result
        mock_llm_chat.start_chat.assert_not_called()
        mock_llm_chat.send_message.assert_not_called()

    def test_generate_daily_prompt_error(
        self, mock_conversation_repo, mock_llm_chat, mock_slack_client, sample_conversation
    ):
        """
        Test the generate_daily_prompt method with an error.
        """
        # Arrange
        service = DailyPromptService(
            conversation_repo=mock_conversation_repo,
            llm_chat=mock_llm_chat,
            slack_client=mock_slack_client,
        )
        mock_llm_chat.send_message.side_effect = Exception("Test error")

        # Act
        result = service.generate_daily_prompt(sample_conversation)

        # Assert
        assert "Error generating daily prompt" in result
        assert "Test error" in result
        mock_llm_chat.start_chat.assert_called_once_with(sample_conversation["messages"])
        mock_llm_chat.send_message.assert_called_once()
