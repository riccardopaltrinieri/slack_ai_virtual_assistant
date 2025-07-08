from datetime import datetime
from typing import Any, Dict, List, Tuple

from app.config.dependencies import get_conversation_repository, get_llm_chat
from app.integrations.slack_client import SlackClient
from app.interfaces.conversation_repository import ConversationRepository
from app.interfaces.llm_chat import LLMChat


class DailyPromptService:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        llm_chat: LLMChat,
        slack_client: SlackClient,
    ):
        """
        Initialize the daily prompt service.
        """
        self.conversation_repo = conversation_repo
        self.llm_chat = llm_chat
        self.slack_client = slack_client

    def get_all_conversations(self) -> List[Dict[str, Any]]:
        """
        Get all conversations from the database.

        Returns:
            A list of all conversations.
        """
        return self.conversation_repo.find_many()

    def trigger_daily_prompt(self) -> Tuple[str, int]:
        print("Scheduled prompt trigger received!")

        try:
            # 1. Fetch all conversations from the database
            conversations = self.get_all_conversations()
            print(f"Found {len(conversations)} conversations")

            # 2. For each conversation, generate a daily prompt
            for conversation in conversations:
                conversation_id = conversation.get("conversation_id", "unknown")
                is_active = conversation.get("active")

                if not is_active:
                    continue

                print(f"Generating daily prompt for conversation {conversation_id}")

                # Generate the daily prompt
                daily_prompt = self.generate_daily_prompt(conversation)

                # 3. Send the daily prompt to the Slack channel
                message = f"{daily_prompt}"
                self.slack_client.send_message(
                    message=message,
                    channel=conversation_id.replace("slack-", ""),
                )

                # Add the daily prompt to the conversation history
                system_message = {
                    "role": "system",
                    "content": f"Daily Prompt: {daily_prompt}",
                    "timestamp": datetime.now(),
                }
                self.conversation_repo.add_message(conversation_id, system_message)

            return "Daily prompts generated and sent successfully", 200
        except Exception as e:
            print(f"Error in daily job: {str(e)}")
            return f"Error: {str(e)}", 500

    def generate_daily_prompt(self, conversation: Dict[str, Any]) -> str:
        """
        Generate a daily prompt for a conversation using Gemini.

        Args:
            conversation: The conversation to generate a prompt for.

        Returns:
            The generated daily prompt.
        """
        conversation_id = conversation.get("conversation_id", "unknown")
        messages = conversation.get("messages", [])

        if not messages:
            return f"No messages found for conversation {conversation_id}"

        # Initialize a new chat session for this conversation
        self.llm_chat.start_chat(messages)

        # Ask Gemini to create a daily prompt based on the conversation history
        prompt_to_gemini = f"""
Today's date ${datetime.now().strftime("%Y-%m-%d %H")}
Craft a brief, friendly, and low-pressure daily check-in message for the user.

Your message should gently invite the user to do one of the following (**but not both**):
1.  Share a thought on their day or some recent events.
2.  Reflect on anything specific that stood out to them recently in the ongoing conversation.

The final message should feel genuinely interested in their journey and not explicitly state it's an "automated message."
Start directly with the check-in.
"""  # noqa E501

        try:
            response = self.llm_chat.send_message(prompt_to_gemini)
            return response
        except Exception as e:
            print(f"Error generating daily prompt for conversation {conversation_id}: {str(e)}")
            return f"Error generating daily prompt: {str(e)}"


daily_prompt_service = DailyPromptService(
    conversation_repo=get_conversation_repository(),
    llm_chat=get_llm_chat(),
    slack_client=SlackClient(),
)
