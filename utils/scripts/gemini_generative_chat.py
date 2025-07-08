#!/usr/bin/env python3
"""
Gemini Chat Script

This script reads the GEMINI_API_KEY from the .env file and uses the
get_gemini_response function from the gemini_wrapper to interact with
the Gemini API.

Usage:
    python scripts/gemini_generative_chat.py

The script will prompt you to enter your question or message, and then
display the response from the Gemini API.
"""

import os
import sys

from dotenv import load_dotenv

from app.integrations.gemini import GeminiChat

load_dotenv()


def main() -> None:
    """Main function to run the Gemini chat script."""
    model = os.getenv("GEMINI_MODEL_NAME") or "models/gemini-2.0-flash"

    # Get the API key from environment variables
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "empty":
        print("Error: GEMINI_API_KEY not set or is empty in .env file")
        print("Please set a valid API key in the .env file")
        sys.exit(1)

    print("Welcome to Gemini Chat!")
    print("Type 'exit' or 'quit' to end the conversation.")

    while True:
        # Get user input
        user_input = input("\nYou: ")

        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        try:
            # Get response from Gemini API
            gemini_chat = GeminiChat(model=model, api_key=api_key)
            gemini_chat.start_chat()
            response = gemini_chat.send_message(message=user_input)

            # Display the response
            print(f"\nGemini: {response}")

        except Exception as e:
            print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
