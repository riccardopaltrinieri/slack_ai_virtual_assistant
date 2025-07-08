#!/usr/bin/env python3
"""
Gemini Chat with Storage Script

This script takes an ID as input, interacts with the Gemini API for a chat
conversation, and stores the conversation in MongoDB. It maintains conversation
context between runs, allowing Gemini to remember previous interactions.

Usage:
    python scripts/gemini_chat_with_storage.py <conversation_id>

The script will prompt you to enter your questions or messages, display
the responses from the Gemini API, and store the entire conversation
in MongoDB under the specified conversation ID.
"""

import argparse
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from app.integrations.gemini import GeminiChat
from app.integrations.mongodb import MongoDBConnection

# Load environment variables from .env file
load_dotenv()


def setup_mongodb() -> MongoDBConnection:
    """
    Set up and connect to MongoDB.

    Returns:
        A connected MongoDB connection instance.

    Raises:
        ConnectionError: If connection to MongoDB fails.
    """
    try:
        # Create a MongoDB connection
        mongo = MongoDBConnection()
        # Connect to MongoDB
        mongo.connect()
        return mongo
    except ConnectionError as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        print("Make sure MongoDB is running and the connection details in .env are correct.")
        print("You can start MongoDB using Docker with: docker-compose up -d mongodb")
        sys.exit(1)


def main() -> None:
    """Main function to run the Gemini chat with storage script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Gemini Chat with MongoDB Storage")
    parser.add_argument("conversation_id", nargs="?", help="Unique identifier for the conversation")
    args = parser.parse_args()

    # Get the conversation ID
    conversation_id = args.conversation_id
    if not conversation_id:
        while True:
            conversation_id = input("Please enter a unique conversation ID: ").strip()
            if conversation_id:
                break
            else:
                print("Conversation ID cannot be empty. Please try again.")

    # Get model and API key from environment variables
    model = os.getenv("GEMINI_MODEL_NAME") or "models/gemini-2.0-flash"
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key == "empty":
        print("Error: GEMINI_API_KEY not set or is empty in .env file")
        print("Please set a valid API key in the .env file")
        sys.exit(1)

    # Set up MongoDB connection
    mongo = setup_mongodb()

    # Collection name for storing conversations
    collection_name = "gemini_conversations"

    # Check if a conversation with this ID already exists
    existing_conversation = mongo.find_one(collection_name, {"conversation_id": conversation_id})

    if existing_conversation:
        # Load existing conversation
        conversation = existing_conversation
        messages = conversation.get("messages", [])
        print(f"Continuing existing conversation with ID: {conversation_id}")
    else:
        initial_llm_context = [
            {
                "role": "user",
                "content": "Add here your prompt",
            },
        ]
        conversation = {
            "conversation_id": conversation_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "messages": initial_llm_context,
        }
        # Insert the new conversation
        mongo.insert_one(collection_name, conversation)
        messages = initial_llm_context
        print(f"Starting new conversation with ID: {conversation_id}")

    # Initialize the Gemini Chat wrapper
    chat = GeminiChat(
        model=model,
        api_key=api_key,
        temperature=0.7,
    )

    # Start a chat session with the existing conversation history
    chat.start_chat(messages)

    print("Welcome to Gemini Chat with Storage!")
    print("Type 'exit' or 'quit' to end the conversation.")

    try:
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            user_message = {
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now(),
            }
            messages.append(user_message)

            try:
                # Send message to Gemini Chat API and get response
                response = chat.send_message(user_input)

                print(f"\nGemini: {response}")

                # Add Gemini response to the conversation
                gemini_message = {
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now(),
                }
                messages.append(gemini_message)

            except Exception as e:
                print(f"Error: {str(e)}")
                # Add error message to the conversation
                error_message = {
                    "role": "system",
                    "content": f"Error: {str(e)}",
                    "timestamp": datetime.now(),
                }
                messages.append(error_message)

            # Update the conversation in MongoDB
            mongo.update_one(
                collection_name,
                {"conversation_id": conversation_id},
                {"$set": {"messages": messages, "updated_at": datetime.now()}},
            )

    finally:
        # Ensure MongoDB connection is closed
        mongo.disconnect()
        print("MongoDB connection closed.")


if __name__ == "__main__":
    main()
