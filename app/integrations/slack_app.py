import logging
from typing import Any

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.oauth import OAuthFlow
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk import WebClient

from app.config.config import config
from app.config.dependencies import get_slack_installation_store, get_slack_state_store
from app.use_cases.slack_chat import slack_service

logger = logging.getLogger(__name__)

oauth_settings = OAuthSettings(
    client_id=config.slack_client_id,
    state_store=get_slack_state_store(),
    client_secret=config.slack_client_secret,
    scopes=[
        "chat:write",
        "app_mentions:read",
        "channels:history",
        "groups:history",
        "im:history",
        "mpim:history",
    ],
    user_scopes=[],  # add user scopes if needed
    redirect_uri=None,  # Bolt will handle this automatically
)
app = App(
    installation_store=get_slack_installation_store(),
    oauth_settings=oauth_settings,
    logger=logger,
    oauth_flow=OAuthFlow(settings=oauth_settings),
)


@app.event("message")
def handle_message_events(body: dict[str, Any], client: WebClient) -> None:
    """
    Handle message events from Slack.

    Args:
        body: The event body from Slack.
        client: WebClient instance for interacting with the Slack API.
    """
    print(f"Handling message event: {body}")
    slack_service.handle_message(body, client)


@app.event("app_mention")
def handle_app_mention_events(body: dict[str, Any], client: WebClient) -> None:
    """
    Handle app_mention events from Slack.

    Args:
        body: The event message body from Slack.
        client: A WebClient instance for interacting with the Slack API.
    """
    print(f"Handling mention event: {body}")
    slack_service.handle_message(body, client)


slack_handler = SlackRequestHandler(app)
