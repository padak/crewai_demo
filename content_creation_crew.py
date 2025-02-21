from dotenv import load_dotenv
import os
import logging
import asyncio
import json
from datetime import datetime
import crewai_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def main(topic: str = "The Future of AI in Healthcare"):
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
            create_editing_task
        )
        logger.info("All components imported successfully")
        
        # Configure the LLM to use OpenRouter
        llm = ChatOpenAI(
            model="meta-llama/llama-3.1-8b-instruct",
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
            verbose=True
        )

        logger.info("Crew initialized successfully")

        try:
            # Execute the crew tasks
            result = content_crew.kickoff()
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