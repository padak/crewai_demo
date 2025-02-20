import logging
import asyncio
import websockets
import json
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional
import sys
from types import MethodType

logger = logging.getLogger(__name__)

# Global configuration
config = {
    "ws_url": "ws://161.35.192.142:8000/ws",
    "initialized": False,
    "topic": None,
    "websocket": None
}

async def send_status_update(message):
    """Send status update to WebSocket server."""
    if not config["initialized"]:
        return
    
    # Add agent state information for UI updates
    enhanced_message = {
        **message,
        "timestamp": datetime.now().isoformat(),
        "type": "status",
        "agent_state": {
            "name": message.get("agent"),
            "status": message.get("task"),
            "role": message.get("agent")  # Use full agent name as role for UI
        }
    }
    
    logger.info(f"Sending status update: {json.dumps(enhanced_message, indent=2)}")
        
    try:
        async with websockets.connect(config["ws_url"]) as websocket:
            await websocket.send(json.dumps(enhanced_message))
    except Exception as e:
        logger.error(f"Failed to send status update: {str(e)}")

def sync_send_status(message):
    """Synchronous wrapper for send_status_update."""
    try:
        asyncio.run(send_status_update(message))
    except Exception as e:
        logger.error(f"Failed to send status update: {str(e)}")

def get_task_info(task):
    """Extract task and agent information."""
    # Map agent roles to UI-expected names
    role_to_name = {
        'Research Analyst': 'Research Agent',
        'Content Writer': 'Writer Agent',
        'Content Editor': 'Editor Agent'
    }
    
    # Get the agent's role
    agent_role = task.agent.role if hasattr(task.agent, 'role') else 'Unknown'
    # Map to UI-expected name
    agent_name = role_to_name.get(agent_role, agent_role)
    logger.info(f"Mapped agent role '{agent_role}' to UI name '{agent_name}'")
    
    description = str(getattr(task, 'description', ''))
    
    # Determine task type based on agent name or task description
    if "research" in agent_name.lower() or "research" in description.lower():
        task_type = "Researching"
    elif "writ" in agent_name.lower() or "writ" in description.lower():
        task_type = "Writing"
    elif "edit" in agent_name.lower() or "edit" in description.lower():
        task_type = "Editing"
    else:
        task_type = "Processing"
    
    logger.info(f"Resolved agent name: {agent_name}, task type: {task_type}")
    return agent_name, task_type

def patch_crewai():
    """Patch CrewAI classes with monitoring capabilities."""
    from crewai import Task, Crew
    
    logger.info("Patching CrewAI Task methods...")
    
    # Store original methods
    original_execute_async = Task.execute_async
    original_execute_sync = Task.execute_sync
    original_crew_kickoff = Crew.kickoff
    
    async def monitored_execute_async(self, *args, **kwargs):
        """Monitored version of async task execution."""
        if not config["initialized"]:
            return await original_execute_async(self, *args, **kwargs)
            
        agent_name, task_type = get_task_info(self)
        
        # Send start status
        sync_send_status({
            "agent": agent_name,
            "task": task_type,
            "output": f"Starting {task_type.lower()} task"
        })
        
        try:
            # Execute the task
            result = await original_execute_async(self, *args, **kwargs)
            
            # Send completion status
            sync_send_status({
                "agent": agent_name,
                "task": "Completed",
                "output": f"Completed {task_type.lower()} task"
            })
            
            return result
        except Exception as e:
            # Send error status
            sync_send_status({
                "agent": agent_name,
                "task": "Error",
                "output": f"Error in {task_type.lower()} task: {str(e)}"
            })
            raise
    
    def monitored_execute_sync(self, *args, **kwargs):
        """Monitored version of sync task execution."""
        if not config["initialized"]:
            return original_execute_sync(self, *args, **kwargs)
            
        agent_name, task_type = get_task_info(self)
        
        # Send start status
        sync_send_status({
            "agent": agent_name,
            "task": task_type,
            "output": f"Starting {task_type.lower()} task"
        })
        
        try:
            # Execute the task
            result = original_execute_sync(self, *args, **kwargs)
            
            # Send completion status
            sync_send_status({
                "agent": agent_name,
                "task": "Completed",
                "output": f"Completed {task_type.lower()} task"
            })
            
            return result
        except Exception as e:
            # Send error status
            sync_send_status({
                "agent": agent_name,
                "task": "Error",
                "output": f"Error in {task_type.lower()} task: {str(e)}"
            })
            raise
    
    def monitored_crew_kickoff(self, *args, **kwargs):
        """Monitored version of Crew kickoff."""
        if not config["initialized"]:
            return original_crew_kickoff(self, *args, **kwargs)
            
        # Send start status
        sync_send_status({
            "agent": "System",
            "task": "Starting",
            "output": f"Beginning content creation for topic: {config['topic']}"
        })
        
        try:
            # Execute the crew tasks
            result = original_crew_kickoff(self, *args, **kwargs)
            
            # Send completion status
            sync_send_status({
                "agent": "System",
                "task": "Completed",
                "output": "Content creation process finished successfully"
            })
            
            return result
        except Exception as e:
            # Send error status
            sync_send_status({
                "agent": "System",
                "task": "Error",
                "output": f"Error in content creation: {str(e)}"
            })
            raise

    # Patch the classes with the monitored versions
    Task.execute_async = monitored_execute_async
    Task.execute_sync = monitored_execute_sync
    Crew.kickoff = monitored_crew_kickoff
    
    logger.info("Successfully patched CrewAI Task and Crew methods")
    return Task, Crew

def init(ws_url: Optional[str] = None, topic: Optional[str] = None):
    """Initialize the monitoring system."""
    if ws_url:
        config["ws_url"] = ws_url
    if topic:
        config["topic"] = topic
    
    # Patch CrewAI classes
    patch_crewai()
    
    # Mark as initialized
    config["initialized"] = True
    
    # Send initial connection status
    sync_send_status({
        "agent": "System",
        "task": "Connection",
        "output": "Monitoring system initialized"
    })
    
    logger.info("CrewAI monitoring initialized successfully") 