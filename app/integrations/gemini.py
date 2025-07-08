"""
Wrapper module for Google's Gemini Chat API.
This module provides a simplified interface to interact with the Gemini API
for chat-based conversations with memory.
"""

from typing import Any, Dict, Iterable, List, Optional

import google.generativeai as genai
from google.generativeai.types import ContentDict, GenerationConfig

from app.interfaces.llm_chat import LLMChat


class GeminiChat(LLMChat):
    """
    A wrapper class for interacting with the Gemini Chat API.

    This class provides methods for creating and managing chat conversations
    with the Gemini API, including maintaining conversation history.
    """

    def __init__(
        self,
        model: str = "models/gemini-2.0-flash",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        safety_settings: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize the Gemini Chat wrapper.

        Args:
            model: The model to use (default: "models/gemini-2.0-flash").
            api_key: The API key to use. If None, the API key must be set in the environment.
            temperature: Controls the randomness of the output (default: 0.7).
            max_output_tokens: The maximum number of tokens to generate.
            top_p: The cumulative probability cutoff for token selection.
            top_k: The number of highest probability tokens to consider for each step.
            safety_settings: Custom safety settings to use.
        """
        # Configure the API key if provided
        if api_key:
            genai.configure(api_key=api_key)

        # Prepare generation config
        self.generation_config = GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_output_tokens,
        )

        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config=self.generation_config,
            safety_settings=safety_settings,
        )

        # Initialize chat session
        self.chat_session = None

    def start_chat(self, messages: Optional[List[dict[str, Any]]] = None) -> None:
        """
        Start a new chat session even if it already exists.

        Args:
            messages: Optional list of message dictionaries with 'role' and 'content' keys.
                    Roles should be either 'user' or 'assistant'.
        """
        # TODO add memory / Retrieval Augmented Generation (RAG) support
        self.chat_session = self.model.start_chat(history=self._convert_history(messages))

    @staticmethod
    def _convert_history(messages: Optional[List[Dict[str, str]]] = None) -> Iterable[ContentDict]:
        """
        Add an assistant message to the chat history.

        Args:
            messages: Optional list of message dictionaries with 'role' and 'content' keys.
                    Roles should be either 'user' or 'assistant'.
        """
        history = []

        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")

            # Skip system and empty messages as they're not supported in the chat API
            if not role or role == "system" or not content:
                continue

            history.append({"role": role, "parts": [{"text": content}]})

        return history

    def send_message(self, message: str) -> str:
        """
        Send a message to the chat session and get the response.

        Args:
            message: The message to send.

        Returns:
            The response from the model.

        Raises:
            ValueError: If no chat session has been started.
            Exception: For other API-related errors.
        """
        if not self.chat_session:
            raise ValueError("No chat session has been started. Call start_chat() first.")

        try:
            # Send the message and get the response
            response = self.chat_session.send_message(message)

            # Return the text response
            return str(response.text)
        except Exception as e:
            # Re-raise the exception with a more informative message
            raise Exception(f"Error sending message to Gemini Chat API: {str(e)}")

    def get_history(self) -> List[Dict[str, str]]:
        """
        Get the chat history in a standardized format.

        Returns:
            A list of message dictionaries with 'role' and 'content' keys.

        Raises:
            ValueError: If no chat session has been started.
        """
        if not self.chat_session:
            raise ValueError("No chat session has been started. Call start_chat() first.")

        history = []

        # Convert the internal history format to our standardized format
        if hasattr(self.chat_session, "history"):
            for message in self.chat_session.history:
                role = message.get("role", "")
                parts = message.get("parts", [])

                if not parts:
                    continue

                content = parts[0].get("text", "") if isinstance(parts[0], dict) else str(parts[0])

                # Map the roles to our standardized format
                standardized_role = "user" if role == "user" else "assistant"

                history.append({"role": standardized_role, "content": content})

        return history
