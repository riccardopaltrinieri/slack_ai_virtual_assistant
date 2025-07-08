from datetime import datetime
from typing import Any, Dict, List, Optional

from google.cloud import firestore
from google.cloud.firestore import Client
from google.cloud.firestore_v1.transaction import Transaction

from app.config.config import config
from app.interfaces.conversation_repository import ConversationRepository, DuplicateMessageError


class FirestoreConnection:
    """
    A wrapper class for Firestore operations.

    This class provides methods for connecting to Firestore and performing
    basic CRUD operations.
    """

    def __init__(
        self,
        client: Client,
        project_id: Optional[str] = None,
    ):
        """
        Initialize the Firestore wrapper.

        Args:
            project_id: Google Cloud project ID. If not provided, uses the default project.
        """
        self.client = client
        self.project_id = project_id or config.google_cloud_project_id

    def disconnect(self) -> None:
        """
        Disconnect from Firestore.
        """
        if self.client:
            # Firestore client doesn't have a close method, but we'll keep this for consistency
            self.client = None

    def get_collection(self, collection_name: str) -> firestore.CollectionReference:
        """
        Get a Firestore collection.

        Args:
            collection_name: Name of the collection.

        Returns:
            The Firestore collection reference.

        Raises:
            ValueError: If not connected to Firestore.
        """
        if self.client is None:
            raise ValueError("Not connected to Firestore. Call connect() first.")
        return self.client.collection(collection_name)

    def insert_one(
        self,
        collection_name: str,
        document: Dict[str, Any],
        document_id: Optional[str] = None,
    ) -> str:
        """
        Insert a single document into a collection.

        Args:
            collection_name: Name of the collection.
            document: Document to insert.
            document_id: Optional ID for the document. If not provided, Firestore will generate one.

        Returns:
            The ID of the inserted document.

        Raises:
            ValueError: If not connected to Firestore.
        """
        collection = self.get_collection(collection_name)
        if document_id:
            doc_ref = collection.document(document_id)
            doc_ref.set(document)
            return document_id
        else:
            doc_ref = collection.add(document)[1]
            return doc_ref.id

    def find_one(
        self,
        collection_name: str,
        query: Dict[str, Any],
        transaction: Transaction | None = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single document in a collection.

        Args:
            collection_name: Name of the collection.
            query: Query to filter documents.
            transaction: The database transaction

        Returns:
            The found document or None if no document matches the query.

        Raises:
            ValueError: If not connected to Firestore.
        """
        collection = self.get_collection(collection_name)
        query_ref = collection

        for field, value in query.items():
            query_ref = query_ref.where(field, "==", value)

        docs = query_ref.limit(1).stream(transaction=transaction)
        for doc in docs:
            return {**doc.to_dict(), "id": doc.id}

        return None

    def find_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents in a collection.

        Args:
            collection_name: Name of the collection.
            query: Query to filter documents.
            limit: Maximum number of documents to return.

        Returns:
            List of found documents.

        Raises:
            ValueError: If not connected to Firestore.
        """
        collection = self.get_collection(collection_name)
        query_ref = collection

        for field, value in query.items():
            query_ref = query_ref.where(field, "==", value)

        if limit:
            query_ref = query_ref.limit(limit)

        docs = query_ref.stream()
        return [{**doc.to_dict(), "id": doc.id} for doc in docs]

    def update_one(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
        transaction: Transaction | None = None,
    ) -> bool:
        """
        Update a single document in a collection.

        Args:
            collection_name: Name of the collection.
            query: Query to filter documents.
            update: Update operations to apply.
            upsert: If True, create a new document if no document matches the query.
            transaction: A database transaction

        Returns:
            True if the document was updated, False otherwise.

        Raises:
            ValueError: If not connected to Firestore.
        """
        doc_id = query.get("id", None)
        if doc_id is None:
            document = self.find_one(collection_name, query, transaction=transaction)
            doc_id = document["id"]

        doc_ref = self.get_collection(collection_name).document(doc_id)

        if doc_ref:
            # Handle $set operator similar to MongoDB
            if "$set" in update:
                update = update["$set"]

            if transaction:
                transaction.update(doc_ref, update)
            else:
                doc_ref.update(update)
            return True
        elif upsert:
            # Create a new document if it doesn't exist
            new_doc = {**query}
            if "$set" in update:
                new_doc.update(update["$set"])
            else:
                new_doc.update(update)

            self.insert_one(collection_name, new_doc)
            return True

        return False

    def delete_one(self, collection_name: str, query: Dict[str, Any]) -> bool:
        """
        Delete a single document from a collection.

        Args:
            collection_name: Name of the collection.
            query: Query to filter documents.

        Returns:
            True if a document was deleted, False otherwise.

        Raises:
            ValueError: If not connected to Firestore.
        """
        document = self.find_one(collection_name, query)

        if document:
            doc_id = document["id"]
            self.get_collection(collection_name).document(doc_id).delete()
            return True

        return False

    def delete_many(self, collection_name: str, query: Dict[str, Any]) -> int:
        """
        Delete multiple documents from a collection.

        Args:
            collection_name: Name of the collection.
            query: Query to filter documents.

        Returns:
            Number of documents deleted.

        Raises:
            ValueError: If not connected to Firestore.
        """
        documents = self.find_many(collection_name, query)
        count = 0

        for doc in documents:
            doc_id = doc["id"]
            self.get_collection(collection_name).document(doc_id).delete()
            count += 1

        return count

    def count_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        """
        Count documents in a collection.

        Args:
            collection_name: Name of the collection.
            query: Query to filter documents.

        Returns:
            Number of documents matching the query.

        Raises:
            ValueError: If not connected to Firestore.
        """
        # Firestore doesn't have a direct count method, so we need to fetch the documents
        documents = self.find_many(collection_name, query)
        return len(documents)


class FirestoreConversationRepository(ConversationRepository):
    """
    Firestore implementation of the conversation store.

    This class provides methods for storing and retrieving conversations and messages from Firestore.
    """

    def __init__(
        self,
        firestore: FirestoreConnection,
        collection_name: str = "conversations",
    ):
        self.firestore = firestore
        self.collection_name = collection_name

    def initialize_conversation(
        self,
        conversation_id: str,
        initial_context: list[dict[str, Any]] | None = None,
    ) -> bool:
        """
        Create a new conversation if it doesn't exist.

        Args:
            conversation_id: The unique identifier for the conversation.
            initial_context: An optional list of initial messages for a new conversation.
        """
        existing_conversation = self.firestore.find_one(self.collection_name, {"conversation_id": conversation_id})

        if not existing_conversation:
            print(f"Starting new conversation with ID: {conversation_id}")
            messages = initial_context if initial_context is not None else []
            conversation = {
                "conversation_id": conversation_id,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "messages": messages,
            }
            self.firestore.insert_one(self.collection_name, conversation)

        return True

    def add_message(self, conversation_id: str, new: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Add a message to a conversation in Firestore with a transaction to ensure atomicity.
        (i.e., don't add the same message twice)

        Args:
            conversation_id: The unique identifier for the conversation.
            new: The message to add to the conversation.

        Returns:
            The updated list of messages in the conversation.
        """
        conversation = self.firestore.find_one(self.collection_name, {"conversation_id": conversation_id})
        if not conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found")

        messages = conversation.get("messages", [])

        if new.get("message_id") is not None and any(
            existing.get("message_id") == new.get("message_id") for existing in messages
        ):
            raise DuplicateMessageError(f"Message {new.get('message_id')} already exists")

        messages.append(new)

        print("appending new message to conversation", new.get("message_id"), datetime.now())
        self.firestore.update_one(
            self.collection_name,
            {"id": conversation.get("id")},
            {"messages": messages, "updated_at": datetime.now()},
        )

        return messages

    def get_messages(self, conversation_id: str) -> list[dict[str, Any]]:
        """
        Get all messages in a conversation.

        Args:
            conversation_id: The unique identifier for the conversation.

        Returns:
            The list of messages in the conversation.
        """
        conversation = self.firestore.find_one(self.collection_name, {"conversation_id": conversation_id})

        if not conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found")

        return conversation.get("messages", [])

    def update_last_github_check(self, conversation_id: str, last_github_check: datetime):
        """
        Update the last GitHub check time for a conversation.
        """
        conversation = self.firestore.find_one(self.collection_name, {"conversation_id": conversation_id})
        if not conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found")

        self.firestore.update_one(
            self.collection_name,
            {"id": conversation.get("id")},
            {"last_github_check": last_github_check.strftime("%Y-%m-%d %H:%M:%S"), "updated_at": datetime.now()},
        )

    def find_many(self) -> List[Dict[str, Any]]:
        """
        Get all conversations.

        Returns:
            The list of conversations.
        """
        return self.firestore.find_many(self.collection_name, {})
