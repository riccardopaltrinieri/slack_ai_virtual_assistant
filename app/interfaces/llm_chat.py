from abc import ABC


class LLMChat(ABC):
    """
    Abstract base class for LLM chat interfaces.
    """

    def start_chat(self, messages: list[dict]) -> None:
        """
        Start a chat session with the given messages.

        Args:
            messages: A list of message dictionaries to initialize the chat session.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    def send_message(self, message: str) -> str:
        """
        Send a message to the chat session and get the response.

        Args:
            message: The message to send.

        Returns:
            The response from the chat session.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_history(self) -> list[dict]:
        """
        Get the chat history.

        Returns:
            A list of message dictionaries representing the chat history.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
