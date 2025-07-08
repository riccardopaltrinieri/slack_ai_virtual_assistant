from unittest.mock import MagicMock

import pytest

# Import mocks first to apply patches before any other imports
# isort: off
from tests.mocks import mock_daily_prompt_service, mock_slack_handler

from app.integrations.slack_client import SlackClient
from app.interfaces.conversation_repository import ConversationRepository
from app.interfaces.llm_chat import LLMChat


@pytest.fixture
def mock_conversation_repo():
    """
    Create a mock conversation repository for testing.
    """
    mock_repo = MagicMock(spec=ConversationRepository)
    return mock_repo


@pytest.fixture
def mock_llm_chat():
    """
    Create a mock LLM chat for testing.
    """
    mock_chat = MagicMock(spec=LLMChat)
    return mock_chat


@pytest.fixture
def mock_slack_client():
    """
    Create a mock Slack client for testing.
    """
    mock_client = MagicMock(spec=SlackClient)
    return mock_client


@pytest.fixture
def mock_web_client():
    """
    Create a mock Slack WebClient for testing.
    """
    mock_client = MagicMock()
    mock_client.chat_postMessage.return_value = {"ts": "test_timestamp"}
    return mock_client


@pytest.fixture
def sample_conversation():
    """
    Create a sample conversation for testing.
    """
    return {
        "conversation_id": "slack-C12345",
        "active": True,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": "Hello, how are you?",
                "user_id": "U12345",
                "message_id": "msg_12345",
                "timestamp": "2023-01-01T12:00:00",
            },
            {
                "role": "assistant",
                "content": "I'm doing well, thank you for asking! How can I help you today?",
                "timestamp": "2023-01-01T12:00:05",
            },
        ],
    }


@pytest.fixture
def sample_slack_event():
    """
    Create a sample Slack event for testing.
    """
    return {
        "type": "message",
        "channel": "C12345",
        "user": "U12345",
        "text": "Hello, how are you?",
        "client_msg_id": "msg_12345",
        "ts": "1609502400.000100",
    }


@pytest.fixture
def sample_slack_threaded_event():
    """
    Create a sample threaded Slack event for testing.
    """
    return {
        "type": "message",
        "channel": "C12345",
        "user": "U12345",
        "text": "This is a threaded reply",
        "client_msg_id": "msg_12346",
        "ts": "1609502500.000100",
        "thread_ts": "1609502400.000100",
    }


@pytest.fixture(autouse=True)
def mock_dependencies(monkeypatch, mock_conversation_repo, mock_llm_chat):
    """
    Mock the dependency functions to avoid connecting to external services.
    This fixture is automatically used in all tests.
    """
    # Mock get_conversation_repository to return our mock repository
    monkeypatch.setattr("app.config.dependencies.get_conversation_repository", lambda: mock_conversation_repo)

    # Mock get_llm_chat to return our mock LLM chat
    monkeypatch.setattr("app.config.dependencies.get_llm_chat", lambda: mock_llm_chat)

    # Mock slack handler to avoid connecting to Slack
    monkeypatch.setattr("app.api.routes.slack_handler", mock_slack_handler)

    # Mock daily_prompt_service to avoid connecting to external services
    monkeypatch.setattr("app.api.routes.daily_prompt_service", mock_daily_prompt_service)
