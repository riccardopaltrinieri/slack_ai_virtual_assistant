from flask import request

from app.config.config import config
from app.integrations.slack_app import slack_handler
from app.use_cases.daily_prompt import daily_prompt_service


def register_routes(app):
    """
    Register all API routes for the Flask application.
    :param app: Flask application instance
    """

    # Slack Routes
    @app.route("/slack/events", methods=["POST"])
    def slack_events():
        return slack_handler.handle(request)

    @app.route("/slack/install", methods=["GET"])
    def install():
        return slack_handler.handle(request)

    @app.route("/slack/oauth_redirect", methods=["GET"])
    def oauth_redirect():
        return slack_handler.handle(request)

    # Miscellaneous Routes
    @app.route("/daily", methods=["GET"])
    def trigger_daily_prompt():
        expected_token = config.cronjob_token
        if request.headers.get("X-Cloud-Scheduler-Token") != expected_token:
            print("Unauthorized cron job trigger attempt!")
            return "Unauthorized", 401
        return daily_prompt_service.trigger_daily_prompt()
