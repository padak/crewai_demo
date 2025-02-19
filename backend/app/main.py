from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from typing import List
import asyncio
from datetime import datetime
import sys
import os
from pathlib import Path
import logging

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from content_creation_crew import main as run_crewai

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: List[WebSocket] = []

logger = logging.getLogger(__name__)

async def broadcast_message(message: dict):
    """Broadcast message to all connected clients."""
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            active_connections.remove(connection)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        active_connections.append(websocket)
        logger.info("New WebSocket connection established")
        
        try:
            # Send initial connection confirmation
            await websocket.send_json({
                "timestamp": datetime.now().isoformat(),
                "agent": "System",
                "task": "Connection",
                "output": "WebSocket connection established"
            })
            
            # Keep connection alive and handle messages
            while True:
                try:
                    data = await websocket.receive_text()
                    # Broadcast received message to all clients
                    await broadcast_message(json.loads(data))
                    # Send acknowledgment
                    await websocket.send_json({
                        "type": "ack",
                        "timestamp": datetime.now().isoformat()
                    })
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    break
        finally:
            if websocket in active_connections:
                active_connections.remove(websocket)
            logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Error in websocket_endpoint: {str(e)}")
        if websocket in active_connections:
            active_connections.remove(websocket)
        raise

class StartRequest(BaseModel):
    topic: str

@app.post("/start")
async def start_crewai(request: StartRequest):
    try:
        # Run CrewAI in a separate thread to not block
        asyncio.create_task(run_crewai_task(request.topic))
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def run_crewai_task(topic: str):
    try:
        # Initial status
        await broadcast_message({
            "timestamp": datetime.now().isoformat(),
            "agent": "System",
            "task": "Starting",
            "output": f"Beginning content creation for topic: {topic}"
        })

        # Update Research Agent status
        await broadcast_message({
            "timestamp": datetime.now().isoformat(),
            "agent": "Research Agent",
            "task": "Researching",
            "output": f"Starting research on topic: {topic}"
        })
        
        # Run CrewAI
        result = await asyncio.to_thread(run_crewai, topic)
        
        # Since we can't directly hook into CrewAI's internal state changes,
        # we'll monitor the output for specific patterns
        if "Writer Agent" in str(result):
            await broadcast_message({
                "timestamp": datetime.now().isoformat(),
                "agent": "Research Agent",
                "task": "Completed",
                "output": "Research phase completed"
            })
            await broadcast_message({
                "timestamp": datetime.now().isoformat(),
                "agent": "Writer Agent",
                "task": "Writing",
                "output": "Creating content based on research findings"
            })

        if "Editor Agent" in str(result):
            await broadcast_message({
                "timestamp": datetime.now().isoformat(),
                "agent": "Writer Agent",
                "task": "Completed",
                "output": "Writing phase completed"
            })
            await broadcast_message({
                "timestamp": datetime.now().isoformat(),
                "agent": "Editor Agent",
                "task": "Editing",
                "output": "Reviewing and optimizing the content"
            })
        
        # Final status update
        await broadcast_message({
            "timestamp": datetime.now().isoformat(),
            "agent": "Editor Agent",
            "task": "Completed",
            "output": "Content optimization completed"
        })

        await broadcast_message({
            "timestamp": datetime.now().isoformat(),
            "agent": "System",
            "task": "Completed",
            "output": "Content creation process finished successfully",
            "type": "status",
            "status": "completed"
        })
        
    except Exception as e:
        error_msg = f"Error in content creation: {str(e)}"
        await broadcast_message({
            "timestamp": datetime.now().isoformat(),
            "agent": "System",
            "task": "Error",
            "output": error_msg,
            "type": "status",
            "status": "error"
        })

@app.get("/")
async def root():
    return {"status": "running"} 