import logging
from google import genai
from app.utils.config import settings

logger = logging.getLogger(__name__)

def get_gemini_client() -> genai.Client:
    """
    Initializes and returns the Google GenAI client instance.
    Raises ValueError if the GEMINI_API_KEY is not set.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key == "your_gemini_api_key_here":
        logger.error("GEMINI_API_KEY is not set in environment or .env file.")
        raise ValueError(
            "GEMINI_API_KEY is missing. Please set it in backend/.env to enable AI agents."
        )
    
    # Initialize the official Google GenAI Client
    return genai.Client(api_key=api_key)
