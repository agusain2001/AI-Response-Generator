# backend/app/services/ai_service.py
import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file in the backend directory
# Assuming .env is in the same directory as this script or a parent accessible one.
# For robustness, specify path if needed, e.g. load_dotenv(dotenv_path="path/to/.env")
# If running from `backend` directory with `uvicorn app.main:app`, .env in `backend` should be found.
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    # Fallback if .env is at the project root when running tests or scripts from root
    load_dotenv()


GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GEMINI_API_KEY:
    logger.warning("GOOGLE_API_KEY not found in environment variables. AI service may not work.")
    # raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Error configuring Gemini API: {e}")
        # raise

# Initialize the GenerativeModel
# Using gemini-1.5-flash as it's generally available and cost-effective
# For older models like 'gemini-pro', ensure it's available for your key.
try:
    model = genai.GenerativeModel('gemini-1.5-flash-latest') # Using the latest flash model
except Exception as e:
    logger.error(f"Error initializing Gemini Model: {e}. Ensure the API key is valid and the model name is correct.")
    model = None # Set model to None if initialization fails

async def generate_text_gemini(prompt: str) -> str:
    """
    Generates text using the Google Gemini API.
    """
    if not model:
        logger.error("Gemini model not initialized. Cannot generate text.")
        return "Error: AI model not available."
    if not GEMINI_API_KEY:
        logger.error("Gemini API Key not configured. Cannot generate text.")
        return "Error: API key not configured."

    try:
        # For gemini-1.5-flash, the structure for sending content is slightly different
        # from older models if you were using `generate_content` directly with a simple string.
        # The model expects a list of parts.
        response = await model.generate_content_async(prompt) # Use async version
        
        # Check for safety ratings and blocked prompts if necessary
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            logger.warning(f"Prompt was blocked. Reason: {response.prompt_feedback.block_reason}")
            return f"Content generation failed: Prompt was blocked due to {response.prompt_feedback.block_reason}."

        # Accessing the text content
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            return "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
        else:
            # Fallback or error handling if the expected structure is not present
            # This can happen if the response is empty or blocked for safety reasons
            # and not caught by prompt_feedback.
            logger.warning(f"Unexpected response structure or empty content from Gemini API. Full response: {response}")
            # Try to access text directly if available (older models might have it here)
            if hasattr(response, 'text') and response.text:
                return response.text
            return "Error: Could not retrieve text from AI response. The content might be blocked or the prompt was problematic."

    except Exception as e:
        logger.error(f"Error during Gemini API call: {e}")
        # Check for specific API errors if possible
        if "API_KEY_INVALID" in str(e) or "PERMISSION_DENIED" in str(e):
             return "Error: AI service request failed due to an API key or permission issue."
        return f"Error: AI service request failed. Details: {str(e)}"


async def get_ai_responses(user_query: str) -> tuple[str, str]:
    """
    Generates a casual and a formal response for a given user query.
    """
    casual_prompt = f"""
    You are a friendly and engaging AI assistant.
    A user asked: "{user_query}"
    Please explain this to them in a casual, easy-to-understand, and creative way.
    Imagine you're talking to a curious friend. Use analogies if they help!
    Keep it concise but informative.
    """

    formal_prompt = f"""
    You are a precise and analytical AI assistant.
    Regarding the query: "{user_query}"
    Provide a formal, structured, and analytical explanation.
    Focus on key concepts, definitions, and implications.
    Use precise language suitable for an academic or professional audience.
    Ensure the information is accurate and well-organized.
    """

    casual_response = await generate_text_gemini(casual_prompt)
    formal_response = await generate_text_gemini(formal_prompt)

    return casual_response, formal_response

if __name__ == '__main__':
    # Example usage (for testing this module directly)
    import asyncio
    async def main_test():
        if not GEMINI_API_KEY or not model:
            print("Skipping ai_service test as API key or model is not configured.")
            return

        test_query = "What is quantum computing?"
        print(f"Testing AI service with query: '{test_query}'")
        casual, formal = await get_ai_responses(test_query)
        print("\n--- Casual Response ---")
        print(casual)
        print("\n--- Formal Response ---")
        print(formal)

    # asyncio.run(main_test()) # Comment out when not testing directly
