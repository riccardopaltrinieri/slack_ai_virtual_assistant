from unittest.mock import patch

import pytest

from app.api.routes import register_routes


@pytest.fixture
def flask_app():
    """
    Create a Flask app for testing.
    """
    from flask import Flask

    app = Flask(__name__)
    register_routes(app)
    return app


@pytest.fixture
def client(flask_app):
    """
    Create a test client for the Flask app.
    """
    return flask_app.test_client()


class TestSlackRoutes:
    """
    Tests for the Slack routes.
    """

    @patch("app.api.routes.slack_handler")
    def test_slack_events(self, mock_slack_handler, client):
        """
        Test the /slack/events route.
        """
        mock_slack_handler.handle.return_value = "OK"

        response = client.post("/slack/events", json={"event": "test_event"})

        assert response.status_code == 200
        assert response.data == b"OK"
        mock_slack_handler.handle.assert_called_once()

    @patch("app.api.routes.slack_handler")
    def test_slack_install(self, mock_slack_handler, client):
        """
        Test the /slack/install route.
        """
        mock_slack_handler.handle.return_value = "Install page"

        response = client.get("/slack/install")

        assert response.status_code == 200
        assert response.data == b"Install page"
        mock_slack_handler.handle.assert_called_once()

    @patch("app.api.routes.slack_handler")
    def test_slack_oauth_redirect(self, mock_slack_handler, client):
        """
        Test the /slack/oauth_redirect route.
        """
        mock_slack_handler.handle.return_value = "OAuth redirect"

        response = client.get("/slack/oauth_redirect")

        assert response.status_code == 200
        assert response.data == b"OAuth redirect"
        mock_slack_handler.handle.assert_called_once()


class TestMiscRoutes:
    """
    Tests for miscellaneous routes.
    """

    @patch("app.api.routes.daily_prompt_service")
    @patch("app.api.routes.config")
    def test_trigger_daily_prompt_unauthorized(self, mock_config, mock_daily_prompt_service, client):
        """
        Test the /daily route with an unauthorized request.
        """
        response = client.get("/daily")
        mock_config.cronjob_token = "test_token"

        assert response.status_code == 401
        assert "Unauthorized" in response.data.decode()
        mock_daily_prompt_service.trigger_daily_prompt.assert_not_called()

    @patch("app.api.routes.daily_prompt_service")
    @patch("app.api.routes.config")
    def test_trigger_daily_prompt_authorized(self, mock_config, mock_daily_prompt_service, client):
        """
        Test the /daily route with an authorized request.
        """
        mock_config.cronjob_token = "test_token"
        mock_daily_prompt_service.trigger_daily_prompt.return_value = ("Success", 200)

        response = client.get("/daily", headers={"X-Cloud-Scheduler-Token": "test_token"})

        assert response.status_code == 200
        assert response.data == b"Success"
        mock_daily_prompt_service.trigger_daily_prompt.assert_called_once()
