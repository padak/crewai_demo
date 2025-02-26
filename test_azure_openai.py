"""
Test script for Azure OpenAI integration.

This script tests the Azure OpenAI integration by creating a simple ChatOpenAI instance
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

def test_azure_openai():
    """Test the Azure OpenAI integration"""
    # Check if we're configured for Azure OpenAI
    llm_provider = os.environ.get("LLM_PROVIDER", "").lower()
    
    if llm_provider != "azure":
        logger.warning("LLM_PROVIDER is not set to 'azure'. This test is intended for Azure OpenAI.")
        logger.warning("Setting LLM_PROVIDER to 'azure' for this test.")
        os.environ["LLM_PROVIDER"] = "azure"
    
    # Get Azure OpenAI configuration
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")
    deployment_id = os.environ.get("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-35-turbo-0125")
    
    if not api_key or not azure_endpoint:
        logger.error("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT must be set for Azure OpenAI")
        return False
    
    try:
        logger.info(f"Creating ChatOpenAI instance with Azure OpenAI")
        logger.info(f"Azure Endpoint: {azure_endpoint}")
        logger.info(f"Deployment ID: {deployment_id}")
        
        # Create ChatOpenAI instance
        chat = ChatOpenAI(
            model=deployment_id,
            openai_api_key=api_key,
            openai_api_version=api_version,
            azure_endpoint=azure_endpoint,
            azure_deployment=deployment_id,
            temperature=0.7,
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
        logger.error(f"Error testing Azure OpenAI: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("Testing Azure OpenAI integration...")
    success = test_azure_openai()
    
    if success:
        logger.info("Azure OpenAI test completed successfully!")
    else:
        logger.error("Azure OpenAI test failed!") 