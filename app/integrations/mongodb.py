"""
MongoDB Wrapper Module

This module provides a wrapper for MongoDB operations, including connection
management and basic CRUD operations.
"""

import os
from typing import Any, Dict, List, Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database


class MongoDBConnection:
    """
    A wrapper class for MongoDB operations.

    This class provides methods for connecting to MongoDB and performing
    basic CRUD operations.
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        db_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ):
        """
        Initialize the MongoDB wrapper.

        Args:
            uri: MongoDB connection URI. If provided, other connection parameters are ignored.
            db_name: Name of the database to connect to.
            username: MongoDB username.
            password: MongoDB password.
            host: MongoDB host.
            port: MongoDB port.
        """
        self.client = None
        self.db = None

        # Use URI if provided, otherwise use individual connection parameters
        if uri:
            self.uri = uri
        else:
            # Get connection parameters from environment variables if not provided
            self.username = username or os.getenv("MONGODB_USERNAME")
            self.password = password or os.getenv("MONGODB_PASSWORD")
            self.host = host or os.getenv("MONGODB_HOST", "localhost")
            self.port = port or int(os.getenv("MONGODB_PORT", "27017"))
            self.db_name = db_name or os.getenv("MONGODB_DATABASE", "default")

            # Construct URI
            if self.username and self.password:
                self.uri = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.db_name}"
            else:
                self.uri = f"mongodb://{self.host}:{self.port}/{self.db_name}"

    def connect(self) -> Database:
        """
        Connect to MongoDB.

        Returns:
            The MongoDB database instance.

        Raises:
            ConnectionError: If connection to MongoDB fails.
        """
        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]
            # Test connection
            self.client.admin.command("ping")
            return self.db
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")

    def disconnect(self) -> None:
        """
        Disconnect from MongoDB.
        """
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a MongoDB collection.

        Args:
            collection_name: Name of the collection.

        Returns:
            The MongoDB collection.

        Raises:
            ValueError: If not connected to MongoDB.
        """
        if self.db is None:
            raise ValueError("Not connected to MongoDB. Call connect() first.")
        return self.db[collection_name]

    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """
        Insert a single document into a collection.

        Args:
            collection_name: Name of the collection.
            document: Document to insert.

        Returns:
            The ID of the inserted document.

        Raises:
            ValueError: If not connected to MongoDB.
        """
        collection = self.get_collection(collection_name)
        result = collection.insert_one(document)
        return str(result.inserted_id)

    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple documents into a collection.

        Args:
            collection_name: Name of the collection.
            documents: List of documents to insert.

        Returns:
            List of IDs of the inserted documents.

        Raises:
            ValueError: If not connected to MongoDB.
        """
        collection = self.get_collection(collection_name)
        result = collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]

    def find_one(
        self,
        collection_name: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Find a single document in a collection.

        Args:
            collection_name: Name of the collection.
            query: Query to filter documents.
            projection: Fields to include or exclude.

        Returns:
            The found document or None if no document matches the query.

        Raises:
            ValueError: If not connected to MongoDB.
        """
        collection = self.get_collection(collection_name)
        return collection.find_one(query, projection)

    def find_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[tuple]] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents in a collection.

        Args:
            collection_name: Name of the collection.
            query: Query to filter documents.
            projection: Fields to include or exclude.
            sort: List of (key, direction) pairs for sorting.
            limit: Maximum number of documents to return.
            skip: Number of documents to skip.

        Returns:
            List of found documents.

        Raises:
            ValueError: If not connected to MongoDB.
        """
        collection = self.get_collection(collection_name)
        cursor = collection.find(query, projection)

        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)

        return list(cursor)

    def update_one(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
    ) -> int:
        """
        Update a single document in a collection.

        Args:
            collection_name: Name of the collection.
            query: Query to filter documents.
            update: Update operations to apply.
            upsert: If True, create a new document if no document matches the query.

        Returns:
            Number of documents modified.

        Raises:
            ValueError: If not connected to MongoDB.
        """
        collection = self.get_collection(collection_name)
        result = collection.update_one(query, update, upsert=upsert)
        return result.modified_count

    def update_many(
        self,
        collection_name: str,
        query: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False,
    ) -> int:
        """
        Update multiple documents in a collection.

        Args:
            collection_name: Name of the collection.
            query: Query to filter documents.
            update: Update operations to apply.
            upsert: If True, create a new document if no document matches the query.

        Returns:
            Number of documents modified.

        Raises:
            ValueError: If not connected to MongoDB.
        """
        collection = self.get_collection(collection_name)
        result = collection.update_many(query, update, upsert=upsert)
        return result.modified_count

    def delete_one(self, collection_name: str, query: Dict[str, Any]) -> int:
        """
        Delete a single document from a collection.

        Args:
            collection_name: Name of the collection.
            query: Query to filter documents.

        Returns:
            Number of documents deleted.

        Raises:
            ValueError: If not connected to MongoDB.
        """
        collection = self.get_collection(collection_name)
        result = collection.delete_one(query)
        return result.deleted_count

    def delete_many(self, collection_name: str, query: Dict[str, Any]) -> int:
        """
        Delete multiple documents from a collection.

        Args:
            collection_name: Name of the collection.
            query: Query to filter documents.

        Returns:
            Number of documents deleted.

        Raises:
            ValueError: If not connected to MongoDB.
        """
        collection = self.get_collection(collection_name)
        result = collection.delete_many(query)
        return result.deleted_count

    def count_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        """
        Count documents in a collection.

        Args:
            collection_name: Name of the collection.
            query: Query to filter documents.

        Returns:
            Number of documents matching the query.

        Raises:
            ValueError: If not connected to MongoDB.
        """
        collection = self.get_collection(collection_name)
        return collection.count_documents(query)

    def aggregate(self, collection_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform an aggregation on a collection.

        Args:
            collection_name: Name of the collection.
            pipeline: Aggregation pipeline.

        Returns:
            Result of the aggregation.

        Raises:
            ValueError: If not connected to MongoDB.
        """
        collection = self.get_collection(collection_name)
        return list(collection.aggregate(pipeline))
