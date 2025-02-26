"""
Test script for CrewAI integration with different LLM providers.

This script tests the integration of different LLM providers with CrewAI.
"""

import os
import logging
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process

# Import the orchestrator service
from orchestrator_service import ContentCreationCrew

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_crewai_integration():
    """Test the CrewAI integration with the configured LLM provider"""
    # Get the LLM provider
    llm_provider = os.environ.get("LLM_PROVIDER", "openrouter").lower()
    logger.info(f"Testing CrewAI integration with LLM provider: {llm_provider}")
    
    try:
        # Create a ContentCreationCrew instance
        crew_instance = ContentCreationCrew(inputs={"topic": "Artificial Intelligence"})
        logger.info("Created ContentCreationCrew instance")
        
        # Get the crew object
        crew = crew_instance.content_crew()
        logger.info(f"Got crew object of type: {type(crew).__name__}")
        
        # Run a simple task to test the integration
        logger.info("Running a simple task to test the integration...")
        result = crew.kickoff()
        
        logger.info(f"Result type: {type(result).__name__}")
        logger.info(f"Result: {result}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing CrewAI integration: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("Testing CrewAI integration...")
    success = test_crewai_integration()
    
    if success:
        logger.info("CrewAI integration test completed successfully!")
    else:
        logger.error("CrewAI integration test failed!") 