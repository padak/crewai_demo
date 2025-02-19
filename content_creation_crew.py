from dotenv import load_dotenv
import os
import logging
import asyncio
import websockets
import json
from datetime import datetime

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

async def send_monitoring_data(agent_name: str, task_type: str, output: str):
    """Send monitoring data to WebSocket server."""
    ws_url = 'ws://161.35.192.142:8000/ws'
    try:
        async with websockets.connect(ws_url, ping_interval=None) as websocket:
            message = {
                "timestamp": datetime.now().isoformat(),
                "agent": agent_name,
                "task": task_type,
                "output": output,
                "type": "status" if agent_name in ["Research Agent", "Writer Agent", "Editor Agent"] else "system"
            }
            try:
                await websocket.send(json.dumps(message))
                logger.info(f"Sent monitoring data for {agent_name}: {task_type}")
                # Wait for acknowledgment
                response = await websocket.recv()
                logger.info(f"Received acknowledgment: {response}")
            except websockets.exceptions.ConnectionClosed:
                logger.error("WebSocket connection closed while sending message")
            except Exception as e:
                logger.error(f"Error sending message: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to connect to WebSocket server at {ws_url}: {str(e)}")

def send_update(agent_name: str, task_type: str, output: str):
    """Synchronous wrapper for sending monitoring data."""
    try:
        asyncio.run(send_monitoring_data(agent_name, task_type, output))
    except Exception as e:
        logger.error(f"Error in send_update: {str(e)}")
        # Continue execution even if monitoring fails
        pass

def main(topic: str = "The Future of AI in Healthcare"):
    try:
        logger.info("Initializing CrewAI content creation pipeline...")
        send_update("System", "Initialization", f"Starting content creation pipeline for topic: {topic}")
        
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
        send_update("System", "Configuration", "LLM configured successfully")

        # Create agents
        logger.info("Creating agents...")
        research_agent = create_research_agent(llm)
        writer_agent = create_writer_agent(llm)
        editor_agent = create_editor_agent(llm)
        logger.info("Agents created successfully")
        send_update("System", "Agent Creation", "All agents created successfully")

        # Create tasks with the specified topic
        logger.info("Creating tasks...")
        
        # Create research task with monitoring
        research_task = create_research_task(
            research_agent, 
            topic,
            lambda: send_update("Research Agent", "Starting", f"Beginning research on topic: {topic}"),
            lambda output: send_update("Research Agent", "Completed", f"Research completed with {len(str(output))} characters")
        )
        
        # Create writing task with monitoring
        writing_task = create_writing_task(
            writer_agent,
            lambda: send_update("Writer Agent", "Starting", "Creating blog post from research"),
            lambda output: send_update("Writer Agent", "Completed", f"Writing completed with {len(str(output))} characters")
        )
        
        # Create editing task with monitoring
        editing_task = create_editing_task(
            editor_agent,
            lambda: send_update("Editor Agent", "Starting", "Reviewing and optimizing content"),
            lambda output: send_update("Editor Agent", "Completed", f"Editing completed with {len(str(output))} characters")
        )
        
        logger.info("Tasks created successfully")
        send_update("System", "Task Creation", "All tasks created successfully")

        # Create the crew
        logger.info("Initializing crew...")
        content_crew = Crew(
            agents=[research_agent, writer_agent, editor_agent],
            tasks=[research_task, writing_task, editing_task],
            verbose=True  # Enable detailed logging
        )

        logger.info("Crew initialized successfully")
        send_update("System", "Crew Creation", "Content creation crew initialized")

        # Run the crew
        logger.info("Starting content creation process...")
        send_update("System", "Process Start", "Beginning content creation process")
        
        try:
            # Execute the crew tasks
            crew_output = content_crew.kickoff()
            
            # Get the final result string
            result = str(crew_output)
            
            # Process and log results
            logger.info("Content creation completed successfully")
            send_update("System", "Process Complete", "Content creation process finished successfully")
            
            print("\n🎯 Final Result:")
            print(result)
            
            # Log output length for monitoring
            result_length = len(result)
            logger.info("Final output length: %d characters", result_length)
            send_update("System", "Final Result", f"Generated content with {result_length} characters")
            
            return result

        except Exception as e:
            error_msg = f"Error during task execution: {str(e)}"
            logger.error(error_msg)
            send_update("System", "Error", error_msg)
            raise

    except Exception as e:
        error_msg = f"Error in content creation pipeline: {str(e)}"
        logger.error(error_msg)
        send_update("System", "Error", error_msg)
        raise

if __name__ == "__main__":
    main() 