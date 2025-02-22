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

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import asyncio
import os
import logging
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from datetime import datetime
import json
from typing import List
from fastapi.middleware.cors import CORSMiddleware

# Create a queue to store logs
log_queue = Queue(maxsize=1000)  # Store last 1000 logs

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                await self.disconnect(connection)

manager = ConnectionManager()

# Custom log handler that will store logs in our queue
class QueueHandler(logging.Handler):
    def format_message(self, message):
        """Format message, preserving JSON structure for Streamlit."""
        try:
            # First check if message is "DEBUG - {json}" format
            if ' - ' in message:
                prefix, json_part = message.split(' - ', 1)
                try:
                    # Try to parse the JSON part
                    json_obj = json.loads(json_part)
                    # Return structured data that Streamlit can handle
                    return {
                        "type": "debug",
                        "prefix": prefix,
                        "data": json_obj
                    }
                except:
                    pass

            # Then check if entire message is JSON
            if (message.strip().startswith('{') and message.strip().endswith('}')) or \
               (message.strip().startswith('[') and message.strip().endswith(']')):
                try:
                    json_obj = json.loads(message)
                    return {
                        "type": "json",
                        "data": json_obj
                    }
                except:
                    pass
            
            # If not JSON, return as regular message
            return {
                "type": "text",
                "data": message
            }
        except:
            return {
                "type": "text",
                "data": message
            }

    def emit(self, record):
        try:
            formatted_message = self.format_message(record.getMessage())
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
                'level': record.levelname,
                'message': formatted_message,
                'logger': record.name
            }
            
            # Add to queue, remove oldest if full
            if log_queue.full():
                log_queue.get()
            log_queue.put(log_entry)
            
            # Broadcast to WebSocket clients
            asyncio.create_task(manager.broadcast(json.dumps(log_entry)))
        except Exception as e:
            print(f"Error in log handler: {str(e)}")

# Configure logging with our custom handler
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
queue_handler = QueueHandler()
logger.addHandler(queue_handler)

# Load environment variables
load_dotenv()

app = FastAPI(title="Content Orchestrator")

# Define a Pydantic model for input validation
class ContentRequest(BaseModel):
    topic: str

# Use a ThreadPoolExecutor to run synchronous code without blocking the event loop
executor = ThreadPoolExecutor(max_workers=1)

# Enhanced logging setup
def setup_comprehensive_logging():
    # Configure root logger to capture everything
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Create our queue handler
    queue_handler = QueueHandler()
    queue_handler.setLevel(logging.INFO)
    
    # Format all logs consistently
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    queue_handler.setFormatter(formatter)
    
    # Add handler to root logger to capture all logs
    root_logger.addHandler(queue_handler)
    
    # Specifically capture CrewAI and agent logs
    crewai_logger = logging.getLogger('crewai')
    crewai_logger.setLevel(logging.INFO)
    
    # Capture langchain logs
    langchain_logger = logging.getLogger('langchain')
    langchain_logger.setLevel(logging.INFO)
    
    # Capture uvicorn logs
    uvicorn_logger = logging.getLogger('uvicorn')
    uvicorn_logger.setLevel(logging.INFO)
    
    return queue_handler

# Update the run_content_creation function to include more detailed logging
def run_content_creation(topic: str):
    """
    This function initializes the monitoring system, creates the LLM and agents, builds the tasks,
    and then executes the content creation crew. The synchronous Crew execution is run safely in a thread.
    """
    logger.info("=== Starting Content Creation Pipeline ===")
    logger.info(f"Topic: {topic}")

    try:
        # Initialize monitoring (if using crewai_monitor)
        crewai_monitor.init(topic=topic)
        logger.info("✓ Monitoring system initialized")

        # Configure the LLM
        logger.info("Configuring LLM...")
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
        logger.info("✓ LLM configured successfully")

        # Create agents
        logger.info("Creating agents...")
        research_agent = create_research_agent(llm)
        logger.info("✓ Research Agent created")
        writer_agent = create_writer_agent(llm)
        logger.info("✓ Writer Agent created")
        editor_agent = create_editor_agent(llm)
        logger.info("✓ Editor Agent created")

        # Create tasks
        logger.info("Creating tasks...")
        research_task = create_research_task(research_agent, topic)
        logger.info("✓ Research task created")
        writing_task = create_writing_task(writer_agent)
        logger.info("✓ Writing task created")
        editing_task = create_editing_task(editor_agent)
        logger.info("✓ Editing task created")

        # Create and initialize the crew
        logger.info("Initializing crew...")
        content_crew = Crew(
            agents=[research_agent, writer_agent, editor_agent],
            tasks=[research_task, writing_task, editing_task],
            verbose=True,
        )
        logger.info("✓ Crew initialized successfully")

        # Execute the content creation pipeline
        logger.info("=== Starting Crew Execution ===")
        result = content_crew.kickoff()
        logger.info("=== Content Creation Completed ===")
        
        # Log a summary of the result
        logger.info(f"Generated content length: {len(str(result))} characters")
        return result

    except Exception as e:
        logger.error(f"❌ Error in content creation pipeline: {str(e)}")
        raise

# Initialize comprehensive logging
queue_handler = setup_comprehensive_logging()

@app.get("/")
async def root():
    """API status endpoint"""
    return {"status": "running"}

@app.get("/logs/data")
async def get_log_data():
    """Get all logs from the queue"""
    return list(log_queue.queue)

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

# Add WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            try:
                # Wait for messages (if any)
                data = await websocket.receive_text()
                # You can process incoming messages here if needed
            except WebSocketDisconnect:
                manager.disconnect(websocket)
                break
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)

# Add CORS middleware with WebSocket support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    # Run the FastAPI app with uvicorn on port 8888
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="info")
