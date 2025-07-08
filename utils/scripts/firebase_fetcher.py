import json
from datetime import datetime

from dotenv import load_dotenv
from google.cloud import firestore

from app.integrations.firestore import FirestoreConnection, FirestoreConversationRepository

load_dotenv()


def convert_timestamps_to_formatted_date(data):
    """
    Recursively convert Firestore timestamp objects to formatted date strings
    """
    if isinstance(data, dict):
        return {key: convert_timestamps_to_formatted_date(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_timestamps_to_formatted_date(item) for item in data]
    elif isinstance(data, firestore.DocumentSnapshot):
        return convert_timestamps_to_formatted_date(data.to_dict())
    elif hasattr(data, "timestamp"):  # Firestore timestamp object
        # Convert to datetime from epoch seconds to regular datetime
        dt = datetime.fromtimestamp(data.timestamp())
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(data, datetime):
        # Handle regular datetime objects
        return data.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return data


def extract_user_messages(user_conversations):
    """
    Extract only content and timestamp from messages with the role 'user'
    """
    messages = []

    for conversation in user_conversations:
        messages = conversation.get("messages", [])
        for message in messages:
            if not message.get("timestamp"):
                continue
            if message.get("role") == "user":
                messages.extend({"content": message.get("content"), "timestamp": message.get("timestamp")})

    return messages


firestore_client = firestore.Client()
firestore_connection = FirestoreConnection(firestore_client)
conversation_store = FirestoreConversationRepository(firestore_connection)
conversations = conversation_store.find_many()
conversations = [conversation for conversation in conversations if conversation.get("is_active")]

# Convert all timestamp fields to formatted dates
formatted_conversations = convert_timestamps_to_formatted_date(conversations)


# Extract and split user messages
user_messages = extract_user_messages(formatted_conversations)
sorted_user_messages = sorted(user_messages, key=lambda x: x["timestamp"])

print(json.dumps(sorted_user_messages, indent=2))
exit()
