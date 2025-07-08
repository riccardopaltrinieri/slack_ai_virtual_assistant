import logging
from functools import lru_cache

from google.cloud import firestore

from app.config.config import config
from app.integrations.firestore import FirestoreConnection, FirestoreConversationRepository
from app.integrations.gemini import GeminiChat

# from app.integrations.github import GithubClient
from app.interfaces.conversation_repository import ConversationRepository
from app.interfaces.llm_chat import LLMChat
from app.use_cases.slack_installation import FirestoreSlackInstallationStore, FirestoreSlackOAuthStateStore

logger = logging.getLogger()

# TODO use a more sophisticated dependency injection framework


@lru_cache()
def get_database_client():
    match config.database_client:
        case "firestore":
            return firestore.Client()
        case _:
            raise ValueError(f"Unsupported database client: {config.database_client}")


@lru_cache()
def get_slack_state_store():
    match config.database_client:
        case "firestore":
            return FirestoreSlackOAuthStateStore(
                datastore_client=get_database_client(),
                logger=logger,
            )
        case _:
            raise ValueError(f"Unsupported database client: {config.database_client}")


@lru_cache()
def get_slack_installation_store():
    match config.database_client:
        case "firestore":
            return FirestoreSlackInstallationStore(
                datastore_client=get_database_client(),
                logger=logger,
            )
        case _:
            raise ValueError(f"Unsupported database client: {config.database_client}")


@lru_cache()
def get_conversation_repository() -> ConversationRepository:
    match config.database_client:
        case "firestore":
            firestore_client = get_database_client()
            firestore_connection = FirestoreConnection(firestore_client)
            return FirestoreConversationRepository(firestore_connection)
        case _:
            raise ValueError(f"Unsupported database client: {config.database_client}")


@lru_cache()
def get_llm_chat() -> LLMChat:
    match config.llm_provider:
        case "gemini":
            return GeminiChat(
                model=config.gemini_model,
                api_key=config.gemini_api_key,
            )
        case _:
            raise ValueError(f"Unsupported LLM provider: {config.llm_provider}")
