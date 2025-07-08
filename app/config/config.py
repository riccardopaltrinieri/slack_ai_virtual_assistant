import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """
    Configuration class for the application.
    """

    # General
    app_name: str = os.getenv("APP_NAME", "app")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    port: int = int(os.getenv("PORT", "3000"))

    # Google Cloud
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT")
    google_cloud_project_id: str = os.getenv("GOOGLE_CLOUD_PROJECT_ID")

    # Slack
    slack_client_id: str = os.getenv("SLACK_CLIENT_ID")
    slack_client_secret: str = os.getenv("SLACK_CLIENT_SECRET")
    slack_bot_token: str = os.getenv("SLACK_BOT_TOKEN")
    slack_app_token: str = os.getenv("SLACK_APP_TOKEN")

    # LLM
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini")
    gemini_model: str = os.getenv("GEMINI_MODEL_NAME", "models/gemini-2.0-flash")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY")

    # Database
    database_client: str = os.getenv("DATABASE_CLIENT", "firestore")
    firestore_project: str = os.getenv("FIRESTORE_PROJECT")

    # static files
    static_files_path: str = os.getenv("STATIC_FILES_PATH", "static/")

    cronjob_token: str = os.getenv("CRONJOB_TOKEN")


config = Config()
