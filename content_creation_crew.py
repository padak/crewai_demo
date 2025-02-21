from dotenv import load_dotenv
import os
import logging
import asyncio
import json
from datetime import datetime
import crewai_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)  # Get the directory containing this file
env_path = os.path.join(project_root, ".env")
logger.info(f"Looking for .env file at: {env_path}")
load_dotenv(dotenv_path=env_path)

# Log environment variables (masked)
logger.info("Environment variables loaded:")
logger.info(f"OPENROUTER_API_KEY present: {'OPENROUTER_API_KEY' in os.environ}")
if not os.environ.get("OPENROUTER_API_KEY"):
    logger.error(
        f"OpenRouter API key missing. Please ensure .env file exists at {env_path} with OPENROUTER_API_KEY."
    )


def main(
    topic: str = "The Future of AI in Healthcare",
    on_research_start=None,
    on_research_complete=None,
    on_writing_start=None,
    on_writing_complete=None,
    on_editing_start=None,
    on_editing_complete=None,
):
    try:
        logger.info("Initializing CrewAI content creation pipeline...")

        # Log CrewAI import
        logger.info("Importing CrewAI components...")
        from crewai import Task, Crew

        logger.info(f"CrewAI Task class available: {Task}")

        # Initialize monitoring with topic BEFORE importing CrewAI components
        logger.info("Initializing monitoring system...")
        crewai_monitor.init(topic=topic)
        logger.info("Monitoring system initialized")

        # Now import remaining components
        logger.info("Importing remaining CrewAI components...")
        from langchain_openai import ChatOpenAI
        from agents.research_agent import create_research_agent
        from agents.writer_agent import create_writer_agent
        from agents.editor_agent import create_editor_agent
        from tasks.content_tasks import (
            create_research_task,
            create_writing_task,
            create_editing_task,
        )

        logger.info("All components imported successfully")

        # Configure the LLM to use OpenRouter
        llm = ChatOpenAI(
            model="openrouter/openai/gpt-4o-mini",
            openai_api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
            model_kwargs={
                "headers": {
                    "HTTP-Referer": "https://github.com/crewai",  # Optional: for rankings
                    "X-Title": "CrewAI Demo",  # Optional: for rankings
                }
            },
        )
        logger.info("LLM configured successfully")

        # Create agents
        logger.info("Creating agents...")
        research_agent = create_research_agent(llm)
        writer_agent = create_writer_agent(llm)
        editor_agent = create_editor_agent(llm)
        logger.info("Agents created successfully")

        # Create tasks with the specified topic
        logger.info("Creating tasks...")
        research_task = create_research_task(research_agent, topic)
        writing_task = create_writing_task(writer_agent)
        editing_task = create_editing_task(editor_agent)
        logger.info("Tasks created successfully")

        # Create the crew
        logger.info("Initializing crew...")
        content_crew = Crew(
            agents=[research_agent, writer_agent, editor_agent],
            tasks=[research_task, writing_task, editing_task],
            verbose=True,
        )

        logger.info("Crew initialized successfully")

        try:
            # Execute the crew tasks
            if on_research_start:
                on_research_start()

            result = content_crew.kickoff()

            if on_research_complete:
                on_research_complete(result)

            if on_writing_start:
                on_writing_start()

            if on_writing_complete:
                on_writing_complete(result)

            if on_editing_start:
                on_editing_start()

            if on_editing_complete:
                on_editing_complete(result)

            return result

        except Exception as e:
            error_msg = f"Error during task execution: {str(e)}"
            logger.error(error_msg)
            raise

    except Exception as e:
        error_msg = f"Error in content creation pipeline: {str(e)}"
        logger.error(error_msg)
        raise


if __name__ == "__main__":
    import sys

    topic = sys.argv[1] if len(sys.argv) > 1 else "The Future of AI in Healthcare"
    main(topic)
