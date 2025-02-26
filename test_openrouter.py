"""
Test script for OpenRouter integration.

This script tests the OpenRouter integration by creating a simple ChatOpenAI instance
and generating a response.
"""

import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_openrouter():
    """Test the OpenRouter integration"""
    # Check if we're configured for OpenRouter
    llm_provider = os.environ.get("LLM_PROVIDER", "").lower()
    
    if llm_provider != "openrouter":
        logger.warning("LLM_PROVIDER is not set to 'openrouter'. This test is intended for OpenRouter.")
        logger.warning("Setting LLM_PROVIDER to 'openrouter' for this test.")
        os.environ["LLM_PROVIDER"] = "openrouter"
    
    # Get OpenRouter configuration
    api_key = os.environ.get("OPENROUTER_API_KEY")
    base_url = os.environ.get("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
    model = os.environ.get("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
    
    if not api_key:
        logger.error("OPENROUTER_API_KEY must be set for OpenRouter")
        return False
    
    try:
        logger.info(f"Creating ChatOpenAI instance with OpenRouter")
        logger.info(f"Base URL: {base_url}")
        logger.info(f"Model: {model}")
        
        # Create ChatOpenAI instance using the LangChain pattern for OpenRouter
        chat = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            base_url=base_url,
            temperature=0.7,
            default_headers={
                "HTTP-Referer": "https://github.com/crewai",
                "X-Title": "CrewAI Demo",
            }
        )
        
        # Create messages
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Write a short poem about artificial intelligence.")
        ]
        
        # Generate response
        logger.info("Generating response...")
        response = chat.invoke(messages)
        
        logger.info(f"Response: {response.content}")
        return True
    except Exception as e:
        logger.error(f"Error testing OpenRouter: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("Testing OpenRouter integration...")
    success = test_openrouter()
    
    if success:
        logger.info("OpenRouter test completed successfully!")
    else:
        logger.error("OpenRouter test failed!") 