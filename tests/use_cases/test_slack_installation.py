from unittest.mock import MagicMock, patch

import pytest
from slack_sdk.oauth.installation_store import Installation

from app.use_cases.slack_installation import FirestoreSlackInstallationStore, FirestoreSlackOAuthStateStore


@pytest.fixture
def mock_firestore_client():
    """
    Create a mock Firestore client for testing.
    """
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_doc = MagicMock()
    mock_client.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_doc
    return mock_client


@pytest.fixture
def mock_logger():
    """
    Create a mock logger for testing.
    """
    return MagicMock()


@pytest.fixture
def sample_installation():
    """
    Create a sample Slack installation for testing.
    """
    return Installation(
        app_id="A12345",
        enterprise_id="E12345",
        team_id="T12345",
        user_id="U12345",
        bot_id="B12345",
        bot_token="xoxb-12345",
        bot_scopes=["chat:write", "channels:read"],
        user_token="xoxp-12345",
        user_scopes=["chat:write"],
        installed_at=1609502400,
    )


class TestFirestoreSlackInstallationStore:
    """
    Tests for the FirestoreSlackInstallationStore class.
    """

    def test_installation_key(self):
        """
        Test the installation_key static method.
        """
        # Test with enterprise installation
        key = FirestoreSlackInstallationStore.installation_key(
            enterprise_id="E12345",
            team_id=None,
            user_id="U12345",
            is_enterprise_install=True,
        )
        assert key == "E12345-U12345"

        # Test with team installation
        key = FirestoreSlackInstallationStore.installation_key(
            enterprise_id=None,
            team_id="T12345",
            user_id="U12345",
            is_enterprise_install=False,
        )
        assert key == "T12345-U12345"

        # Test with suffix
        key = FirestoreSlackInstallationStore.installation_key(
            enterprise_id=None,
            team_id="T12345",
            user_id="U12345",
            suffix="test",
            is_enterprise_install=False,
        )
        assert key == "T12345-U12345-test"

    def test_bot_key(self):
        """
        Test the bot_key static method.
        """
        # Test with enterprise installation
        key = FirestoreSlackInstallationStore.bot_key(
            enterprise_id="E12345",
            team_id=None,
            is_enterprise_install=True,
        )
        assert key == "E12345-none"

        # Test with team installation
        key = FirestoreSlackInstallationStore.bot_key(
            enterprise_id=None,
            team_id="T12345",
            is_enterprise_install=False,
        )
        assert key == "none-T12345"

        # Test with suffix
        key = FirestoreSlackInstallationStore.bot_key(
            enterprise_id=None,
            team_id="T12345",
            suffix="test",
            is_enterprise_install=False,
        )
        assert key == "none-T12345-test"

    def test_save(self, mock_firestore_client, mock_logger, sample_installation):
        """
        Test the save method.
        """
        # Arrange
        store = FirestoreSlackInstallationStore(
            datastore_client=mock_firestore_client,
            logger=mock_logger,
        )
        mock_doc = mock_firestore_client.collection.return_value.document.return_value

        # Act
        store.save(sample_installation)

        # Assert
        # Check that collections were accessed
        assert mock_firestore_client.collection.call_count >= 2
        assert "installations" in [call[0][0] for call in mock_firestore_client.collection.call_args_list]
        assert "bots" in [call[0][0] for call in mock_firestore_client.collection.call_args_list]

        # Check that documents were created and data was set
        assert mock_firestore_client.collection.return_value.document.call_count >= 2
        assert mock_doc.set.call_count >= 2

    def test_find_bot(self, mock_firestore_client, mock_logger):
        """
        Test the find_bot method.
        """
        # Arrange
        store = FirestoreSlackInstallationStore(
            datastore_client=mock_firestore_client,
            logger=mock_logger,
        )
        mock_doc = mock_firestore_client.collection.return_value.document.return_value
        mock_doc.get.return_value.exists = True

        # Create a mock timestamp that can be converted to a timestamp
        class MockTimestamp:
            def timestamp(self):
                return 1609502400

        mock_doc.get.return_value.to_dict.return_value = {
            "app_id": "A12345",
            "enterprise_id": "E12345",
            "team_id": "T12345",
            "bot_id": "B12345",
            "bot_token": "xoxb-12345",
            "bot_scopes": ["chat:write", "channels:read"],
            "installed_at": MockTimestamp(),
            "bot_user_id": "U12345",  # Required by the Bot class
        }

        # Act
        bot = store.find_bot(
            enterprise_id="E12345",
            team_id="T12345",
            is_enterprise_install=False,
        )

        # Assert
        assert bot is not None
        assert bot.app_id == "A12345"
        assert bot.bot_token == "xoxb-12345"
        mock_firestore_client.collection.assert_called_with("bots")
        mock_firestore_client.collection.return_value.document.assert_called_once()
        mock_doc.get.assert_called_once()

    def test_find_bot_not_found(self, mock_firestore_client, mock_logger):
        """
        Test the find_bot method when the bot is not found.
        """
        # Arrange
        store = FirestoreSlackInstallationStore(
            datastore_client=mock_firestore_client,
            logger=mock_logger,
        )
        mock_doc = mock_firestore_client.collection.return_value.document.return_value
        mock_doc.get.return_value.exists = False

        # Act
        bot = store.find_bot(
            enterprise_id="E12345",
            team_id="T12345",
            is_enterprise_install=False,
        )

        # Assert
        assert bot is None
        mock_firestore_client.collection.assert_called_with("bots")
        mock_firestore_client.collection.return_value.document.assert_called_once()
        mock_doc.get.assert_called_once()

    def test_find_installation(self, mock_firestore_client, mock_logger):
        """
        Test the find_installation method.
        """
        # Arrange
        store = FirestoreSlackInstallationStore(
            datastore_client=mock_firestore_client,
            logger=mock_logger,
        )
        mock_doc = mock_firestore_client.collection.return_value.document.return_value
        mock_doc.get.return_value.exists = True

        # Create a mock timestamp that can be converted to a timestamp
        class MockTimestamp:
            def timestamp(self):
                return 1609502400

        mock_doc.get.return_value.to_dict.return_value = {
            "app_id": "A12345",
            "enterprise_id": "E12345",
            "team_id": "T12345",
            "user_id": "U12345",
            "bot_id": "B12345",
            "bot_token": "xoxb-12345",
            "bot_scopes": ["chat:write", "channels:read"],
            "user_token": "xoxp-12345",
            "user_scopes": ["chat:write"],
            "installed_at": MockTimestamp(),
            "bot_user_id": "U12345",  # Required by the Installation class
            "is_enterprise_install": False,  # Required by the Installation class
        }

        # Act
        installation = store.find_installation(
            enterprise_id="E12345",
            team_id="T12345",
            user_id="U12345",
            is_enterprise_install=False,
        )

        # Assert
        assert installation is not None
        assert installation.app_id == "A12345"
        assert installation.user_token == "xoxp-12345"
        mock_firestore_client.collection.assert_called_with("installations")
        mock_firestore_client.collection.return_value.document.assert_called_once()
        mock_doc.get.assert_called_once()


class TestFirestoreSlackOAuthStateStore:
    """
    Tests for the FirestoreSlackOAuthStateStore class.
    """

    @patch("uuid.uuid4")
    def test_issue(self, mock_uuid, mock_firestore_client, mock_logger):
        """
        Test the issue method.
        """
        # Arrange
        store = FirestoreSlackOAuthStateStore(
            datastore_client=mock_firestore_client,
            logger=mock_logger,
        )
        mock_uuid.return_value = "test-uuid"
        mock_doc = mock_firestore_client.collection.return_value.document.return_value

        # Act
        state = store.issue()

        # Assert
        assert state == "test-uuid"
        mock_firestore_client.collection.assert_called_with("oauth_state_values")
        mock_firestore_client.collection.return_value.document.assert_called_once_with("test-uuid")
        mock_doc.set.assert_called_once_with({"value": "test-uuid"})

    def test_consume_valid_state(self, mock_firestore_client, mock_logger):
        """
        Test the consume method with a valid state.
        """
        # Arrange
        store = FirestoreSlackOAuthStateStore(
            datastore_client=mock_firestore_client,
            logger=mock_logger,
        )
        mock_doc_ref = mock_firestore_client.collection.return_value.document.return_value
        mock_doc_ref.get.return_value.exists = True

        # Act
        result = store.consume("test-state")

        # Assert
        assert result is True
        mock_firestore_client.collection.assert_called_with("oauth_state_values")
        mock_firestore_client.collection.return_value.document.assert_called_once_with("test-state")
        mock_doc_ref.get.assert_called_once()
        mock_doc_ref.delete.assert_called_once()

    def test_consume_invalid_state(self, mock_firestore_client, mock_logger):
        """
        Test the consume method with an invalid state.
        """
        # Arrange
        store = FirestoreSlackOAuthStateStore(
            datastore_client=mock_firestore_client,
            logger=mock_logger,
        )
        mock_doc = mock_firestore_client.collection.return_value.document.return_value
        mock_doc.get.return_value.exists = False

        # Act
        result = store.consume("test-state")

        # Assert
        assert result is False
        mock_firestore_client.collection.assert_called_with("slack_oauth_states")
        mock_firestore_client.collection.return_value.document.assert_called_once_with("test-state")
        mock_doc.get.assert_called_once()
        mock_doc.delete.assert_not_called()
