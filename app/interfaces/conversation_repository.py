"""
Conversation store module for managing conversations in a database.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List


class DuplicateMessageError(Exception):
    pass


class ConversationRepository(ABC):
    """
    Abstract base class for conversation stores.

    This class defines the interface for storing and retrieving conversations.
    """

    @abstractmethod
    def initialize_conversation(
        self,
        conversation_id: str,
        initial_context: List[dict[str, Any]] = None,
    ) -> bool:
        """
        Get an existing conversation or create a new one.

        Args:
            conversation_id: The unique identifier for the conversation.
            initial_context: An optional list of initial messages for a new conversation.

        Returns:
            A tuple containing the conversation document and the messages list.
        """
        pass

    @abstractmethod
    def add_message(self, conversation_id: str, message: dict[str, Any]) -> List[dict[str, Any]]:
        """
        Add a message to a conversation.

        Args:
            conversation_id: The unique identifier for the conversation.
            message: The message to add to the conversation.

        Returns:
            The updated list of messages in the conversation.
        """
        pass

    @abstractmethod
    def get_messages(self, conversation_id: str) -> List[dict[str, Any]]:
        """
        Get all messages in a conversation.

        Args:
            conversation_id: The unique identifier for the conversation.

        Returns:
            The list of messages in the conversation.
        """
        pass

    def find_many(self) -> List[Dict[str, Any]]:
        """
        Get all conversations.

        Returns:
            The list of conversations.
        """
        pass

    def update_last_github_check(self, conversation_id: str, last_github_check: datetime):
        """
        Update the last GitHub check time for a conversation.
        """
        pass
