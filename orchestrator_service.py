# Import CrewAI components and agents/tasks from your codebase
from crewai import Crew
from langchain_openai import ChatOpenAI
from agents.research_agent import create_research_agent
from agents.writer_agent import create_writer_agent
from agents.editor_agent import create_editor_agent
from tasks.content_tasks import (
    create_research_task,
    create_writing_task,
    create_editing_task,
)

import os
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def create_content(topic: str) -> Dict[str, Any]:
    """
    Main function for content creation that can be called via the wrapper.
    Args:
        topic: The topic to create content about
    Returns:
        Dictionary with content and execution details
    """
    logger.info(f"Starting content creation for topic: {topic}")
    try:
        # Configure LLM
        llm = ChatOpenAI(
            model="openrouter/openai/gpt-4o-mini",
            openai_api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
            model_kwargs={
                "headers": {
                    "HTTP-Referer": "https://github.com/crewai",
                    "X-Title": "CrewAI Demo",
                }
            },
        )

        # Create agents
        research_agent = create_research_agent(llm)
        writer_agent = create_writer_agent(llm)
        editor_agent = create_editor_agent(llm)

        # Create tasks
        research_task = create_research_task(research_agent, topic)
        writing_task = create_writing_task(writer_agent)
        editing_task = create_editing_task(editor_agent)

        # Create and run crew
        content_crew = Crew(
            agents=[research_agent, writer_agent, editor_agent],
            tasks=[research_task, writing_task, editing_task],
            verbose=True,
        )

        result = content_crew.kickoff()
        
        # Convert result to string
        if hasattr(result, 'raw'):
            content = str(result.raw)
        else:
            content = str(result)

        return {
            "status": "success",
            "content": content,
            "length": len(content),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in content creation: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": e.__class__.__name__,
            "timestamp": datetime.now().isoformat()
        }

def get_status() -> Dict[str, Any]:
    """
    Get the current status of the service.
    """
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }
