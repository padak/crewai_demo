from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

from crewai import Crew
from langchain_openai import ChatOpenAI

# Import agents
from agents.research_agent import create_research_agent
from agents.writer_agent import create_writer_agent
from agents.editor_agent import create_editor_agent

# Import tasks
from tasks.content_tasks import (
    create_research_task,
    create_writing_task,
    create_editing_task
)

def task_output_handler(output: str) -> None:
    """Handle task output with custom logging."""
    logger.info("Task completed with output length: %d", len(output))
    logger.debug("Task output: %s", output)

def main():
    try:
        logger.info("Initializing CrewAI content creation pipeline...")
        
        # Configure the LLM to use OpenRouter
        llm = ChatOpenAI(
            model="openai/gpt-4-turbo",
            openai_api_key=os.environ["OPENROUTER_API_KEY"],
            openai_api_base=os.environ["OPENAI_API_BASE"],
            model_kwargs={
                "headers": {
                    "HTTP-Referer": "https://github.com/crewai",
                    "X-Title": "CrewAI Demo"
                }
            }
        )
        logger.info("LLM configured successfully")

        # Create agents with monitoring
        logger.info("Creating agents...")
        research_agent = create_research_agent(llm)
        writer_agent = create_writer_agent(llm)
        editor_agent = create_editor_agent(llm)
        logger.info("Agents created successfully")

        # Create tasks with output handling
        logger.info("Creating tasks...")
        research_task = create_research_task(research_agent)
        writing_task = create_writing_task(writer_agent)
        editing_task = create_editing_task(editor_agent)
        logger.info("Tasks created successfully")

        # Create the crew with verbose mode
        logger.info("Initializing crew...")
        content_crew = Crew(
            agents=[research_agent, writer_agent, editor_agent],
            tasks=[research_task, writing_task, editing_task],
            verbose=True  # Enable detailed logging
        )
        logger.info("Crew initialized successfully")

        # Run the crew
        logger.info("Starting content creation process...")
        result = content_crew.kickoff()
        
        # Process and log results
        logger.info("Content creation completed successfully")
        print("\n🎯 Final Result:")
        print(result)
        
        # Log output length for monitoring
        logger.info("Final output length: %d characters", len(result))
        
        return result

    except Exception as e:
        logger.error("Error in content creation pipeline: %s", str(e))
        raise

if __name__ == "__main__":
    main() 