"""
SlackBot module for handling interactions between Slack and LLMs.
"""

import json
import os
from datetime import datetime
from typing import Any

from slack_sdk import WebClient

from app.config.config import config
from app.config.dependencies import get_conversation_repository, get_llm_chat
from app.interfaces.conversation_repository import ConversationRepository, DuplicateMessageError
from app.interfaces.llm_chat import LLMChat


class HandleMessageError(Exception):
    def __init__(self, exception: Exception, placeholder_ts: str | None = None, thread_ts: str | None = None):
        super().__init__()
        self.exception = exception
        self.placeholder_ts = placeholder_ts
        self.thread_ts = thread_ts


INITIAL_CONTEXT_PATH = "initial_context.json"


class SlackService:
    """
    A class for handling interactions between Slack and LLMs.

    This class provides methods for processing Slack messages, sending them to an LLM,
    and storing the conversation in a database.
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        llm_chat: LLMChat,
    ):
        """
        Initialize the SlackBot.

        Args:
            conversation_repo: The conversation repository to use for storing conversations.
            llm_chat: The LLM chat wrapper to use for generating responses.
        """
        self.conversation_repo = conversation_repo
        self.llm_chat = llm_chat

        # Load initial context if provided
        initial_context_path = os.path.join(config.static_files_path, INITIAL_CONTEXT_PATH)
        if os.path.exists(initial_context_path):
            with open(initial_context_path, "r") as f:
                self.initial_context = json.load(f)

    def initialize_conversation(self, conversation_id: str) -> None:
        self.conversation_repo.initialize_conversation(
            conversation_id=conversation_id, initial_context=self.initial_context
        )

    def handle_message(self, event: dict[str, Any], client: WebClient):
        """
        Handle a message from Slack.

        Args:
            event: The message from Slack.
            client: The WebClient instance for interacting with the Slack API.
        """
        # Get the channel ID for the conversation ID
        channel = event.get("channel")
        conversation_id = f"slack-{channel}"

        # Initialize the conversation if it's the first message
        if not hasattr(self, f"initialized_{conversation_id}"):
            self.initialize_conversation(conversation_id)
            setattr(self, f"initialized_{conversation_id}", True)

        text = event.get("text", "")
        # Get the thread_ts if this is a threaded message
        thread_ts = event.get("thread_ts")

        # Add the user message to the conversation
        user_message = {
            "role": "user",
            "content": text,
            "user_id": event.get("user", "unknown"),
            "message_id": event.get("client_msg_id"),
            "timestamp": datetime.now(),
        }
        try:
            messages = self.conversation_repo.add_message(conversation_id, user_message)
        except DuplicateMessageError as exc:
            # The message has already been added to the conversation
            print(exc)
            return None

        placeholder = client.chat_postMessage(
            channel=channel,
            mrkdwn=True,
            text=":hourglass_flowing_sand: _Thinking..._",
            blocks=self._get_context_block(":hourglass_flowing_sand: _Thinking..._"),
            thread_ts=thread_ts,
        )

        try:
            # Make sure we have a chat session with the proper context
            self.llm_chat.start_chat(messages)

            # Send a message to LLM and get the response
            response = self.llm_chat.send_message(text)
            print(f"LLM response: {response}")

            # Add LLM response to the conversation
            llm_message = {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now(),
            }
            self.conversation_repo.add_message(conversation_id, llm_message)

            client.chat_update(
                channel=channel,
                text=response,
                ts=placeholder["ts"],
                thread_ts=thread_ts,
                blocks=self._get_markdown_block(response),
            )
            return None
        except Exception as e:
            raise HandleMessageError(
                exception=e,
                placeholder_ts=placeholder["ts"],
                thread_ts=thread_ts,
            )

    @staticmethod
    def _get_context_block(msg: str):
        return [
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": msg,
                    }
                ],
            }
        ]

    @staticmethod
    def _get_markdown_block(msg: str):
        return [
            {
                "type": "markdown",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": msg,
                    }
                ],
            }
        ]


slack_service = SlackService(
    conversation_repo=get_conversation_repository(),
    llm_chat=get_llm_chat(),
)
