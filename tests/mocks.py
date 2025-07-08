"""
Mock implementations of external dependencies for testing.
"""

import os
from unittest.mock import MagicMock

# Patch the environment to prevent Firestore from trying to connect
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "fake_credentials.json"

# Create a mock Firestore client
mock_firestore_client = MagicMock()
mock_firestore_collection = MagicMock()
mock_firestore_document = MagicMock()
mock_firestore_client.collection.return_value = mock_firestore_collection
mock_firestore_collection.document.return_value = mock_firestore_document

# Create a mock for the slack_handler
mock_slack_handler = MagicMock()
mock_slack_handler.handle.return_value = "OK"

# Create a mock for the daily_prompt_service
mock_daily_prompt_service = MagicMock()
mock_daily_prompt_service.trigger_daily_prompt.return_value = ("Success", 200)


# Patch the firestore.Client to return our mock
def patch_firestore():
    """
    Patch the firestore.Client to return our mock.
    """
    import google.cloud.firestore

    original_client = google.cloud.firestore.Client
    google.cloud.firestore.Client = lambda *args, **kwargs: mock_firestore_client
    return original_client


# Apply the patch when this module is imported
original_firestore_client = patch_firestore()
