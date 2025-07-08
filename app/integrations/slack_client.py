"""
Slack sender module for sending messages to Slack channels through a Slack bot.
This module provides a simplified interface to interact with the Slack API
for sending messages to channels.
"""

from typing import Any

import requests

from app.config.config import config


class SlackClient:
    """
    A class for sending messages to Slack channels through a Slack bot.

    This class provides methods for sending messages to Slack channels
    using a Slack bot token.
    """

    def __init__(
        self,
        default_channel: str | None = None,
    ):
        """
        Initialize the Slack sender.

        Args:
            default_channel: The default channel to send messages to.
        """
        self.default_channel = default_channel
        self.base_url = "https://slack.com/api"

    def send_message(
        self,
        message: str,
        channel: str | None = None,
        thread_ts: str | None = None,
        blocks: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Send a message to a Slack channel.

        Args:
            message: The message text to send.
            channel: The channel to send the message to. If None, uses the default channel.
            thread_ts: The thread timestamp to reply to. If None, starts a new thread.
            blocks: Optional blocks for rich formatting. See Slack API docs for format.

        Returns:
            The response from the Slack API.

        Raises:
            ValueError: If no channel is specified and no default channel is set.
            Exception: For API-related errors.
        """
        if not channel and not self.default_channel:
            raise ValueError("No channel specified and no default channel set.")

        target_channel = channel or self.default_channel

        # Prepare the payload
        payload = {
            "channel": target_channel,
            "text": message,
        }

        # Add thread_ts if provided
        if thread_ts:
            payload["thread_ts"] = thread_ts

        # Add blocks if provided
        if blocks:
            payload["blocks"] = blocks

        # Send the request
        try:
            print(f"Sending message to {target_channel}: {payload}")
            response = requests.post(
                f"{self.base_url}/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {config.slack_bot_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            print("Slack response:", response.json())
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Error sending message to Slack API: {str(e)}")

    def upload_file(
        self,
        file_path: str,
        channel: str | None = None,
        title: str | None = None,
        initial_comment: str | None = None,
        thread_ts: str | None = None,
    ) -> dict[str, Any]:
        """
        Upload a file to a Slack channel.

        Args:
            file_path: The path to the file to upload.
            channel: The channel to upload the file to. If None, uses the default channel.
            title: The title of the file.
            initial_comment: A comment to add to the file.
            thread_ts: The thread timestamp to reply to. If None, starts a new thread.

        Returns:
            The response from the Slack API.

        Raises:
            ValueError: If no channel is specified and no default channel is set.
            FileNotFoundError: If the file does not exist.
            Exception: For API-related errors.
        """
        if not channel and not self.default_channel:
            raise ValueError("No channel specified and no default channel set.")

        target_channel = channel or self.default_channel

        # Check if a file exists
        try:
            with open(file_path, "rb") as file:
                files = {"file": file}

                # Prepare the payload
                payload = {
                    "channels": target_channel,
                }

                # Add optional parameters if provided
                if title:
                    payload["title"] = title
                if initial_comment:
                    payload["initial_comment"] = initial_comment
                if thread_ts:
                    payload["thread_ts"] = thread_ts

                # Send the request
                response = requests.post(
                    f"{self.base_url}/files.upload",
                    headers={
                        "Authorization": f"Bearer {config.slack_bot_token}",
                    },
                    data=payload,
                    files=files,
                )
                response.raise_for_status()
                return response.json()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except requests.RequestException as e:
            raise Exception(f"Error uploading file to Slack API: {str(e)}")
