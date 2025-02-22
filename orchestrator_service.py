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
import crewai_monitor

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import asyncio
import os
import logging
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Load environment variables and configure logging
load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


app = FastAPI(title="Content Orchestrator")


# Define a Pydantic model for input validation
class ContentRequest(BaseModel):
    topic: str


# Use a ThreadPoolExecutor to run synchronous code without blocking the event loop
executor = ThreadPoolExecutor(max_workers=1)


def run_content_creation(topic: str):
    """
    This function initializes the monitoring system, creates the LLM and agents, builds the tasks,
    and then executes the content creation crew. The synchronous Crew execution is run safely in a thread.
    """
    logger.info("Initializing CrewAI content creation pipeline for topic: %s", topic)

    # Initialize monitoring (if using crewai_monitor)
    # crewai_monitor.init(topic=topic)
    # logger.info("Monitoring system initialized")

    # Configure the LLM using the OpenRouter API key from environment variables
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
    logger.info("LLM configured successfully")

    # Create agents using your existing functions
    research_agent = create_research_agent(llm)
    writer_agent = create_writer_agent(llm)
    editor_agent = create_editor_agent(llm)
    logger.info("Agents created successfully")

    # Create tasks for each agent
    research_task = create_research_task(research_agent, topic)
    writing_task = create_writing_task(writer_agent)
    editing_task = create_editing_task(editor_agent)
    logger.info("Tasks created successfully")

    # Create and initialize the crew
    content_crew = Crew(
        agents=[research_agent, writer_agent, editor_agent],
        tasks=[research_task, writing_task, editing_task],
        verbose=True,
    )
    logger.info("Crew initialized successfully - kicking off the pipeline")

    # Execute the content creation pipeline (this is synchronous)
    result = content_crew.kickoff()
    logger.info("Content creation completed")
    return result


@app.post("/create-content")
async def create_content(request: ContentRequest):
    """
    Main endpoint for content creation. Accepts a topic and returns the final content.
    """
    topic = request.topic
    try:
        # Run the content creation synchronously in a thread pool to avoid blocking
        result = await asyncio.get_event_loop().run_in_executor(
            executor, run_content_creation, topic
        )
        return {"content": result}
    except Exception as e:
        logger.error("Error in content creation: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the FastAPI app on port 8888. The endpoint can be tested with curl, Postman, or integrated in a Streamlit app.
    uvicorn.run(app, host="127.0.0.1", port=8888)
