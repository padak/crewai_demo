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
    
    # Log incoming message before any modification
    logger.info(f"STATUS DEBUG - Original message: {json.dumps(message, indent=2)}")
    
    # Get the status from the explicit status field or task field
    status = message.get("status", message.get("task"))
    if status == "Completed":
        status = "Done"  # Use "Done" for completed tasks in UI
    
    # Track status transition
    logger.info(f"STATUS DEBUG - Status normalized from '{message.get('task')}' to '{status}'")
    
    # Get the original task type for active status
    agent_name = message.get("agent")
    
    # Add agent state information for UI updates
    enhanced_message = {
        **message,
        "timestamp": datetime.now().isoformat(),
        "type": "status",
        "task": status,  # Use normalized status
        "agent_state": {
            "name": agent_name,
            "status": status,  # Use the normalized status directly
            "role": agent_name  # Use full agent name as role for UI
        }
    }
    
    logger.info(f"STATUS DEBUG - Final message to send: {json.dumps(enhanced_message, indent=2)}")
        
    try:
        async with websockets.connect(config["ws_url"]) as websocket:
            await websocket.send(json.dumps(enhanced_message))
            logger.info(f"STATUS DEBUG - Successfully sent message for agent {agent_name} with status {status}")
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
    
    description = str(getattr(task, 'description', ''))
    
    # Determine task type based on agent name and description
    if "research" in agent_name.lower():
        task_type = "Researching"
    elif "writer" in agent_name.lower() or "content writer" in agent_role.lower():
        task_type = "Writing"
    elif "editor" in agent_name.lower() or "edit" in description.lower():
        task_type = "Editing"
    else:
        task_type = "Processing"
    
    logger.info(f"TASK DEBUG - Agent '{agent_name}' (role: '{agent_role}') resolved task type: '{task_type}'")
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
        logger.info(f"EXECUTION DEBUG - Starting async execution for {agent_name}")
        
        # Send start status
        sync_send_status({
            "agent": agent_name,
            "task": task_type,
            "output": f"Starting {task_type.lower()} task",
            "status": task_type  # Add explicit status field
        })
        
        try:
            # Execute the task
            result = await original_execute_async(self, *args, **kwargs)
            
            logger.info(f"EXECUTION DEBUG - Completed async execution for {agent_name}")
            # Send completion status
            sync_send_status({
                "agent": agent_name,
                "task": "Done",  # Send Done directly instead of Completed
                "output": f"Completed {task_type.lower()} task",
                "status": "Done"  # Add explicit status field
            })
            
            return result
        except Exception as e:
            logger.error(f"EXECUTION DEBUG - Error in async execution for {agent_name}: {str(e)}")
            # Send error status
            sync_send_status({
                "agent": agent_name,
                "task": "Error",
                "output": f"Error in {task_type.lower()} task: {str(e)}",
                "status": "Error"  # Add explicit status field
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
            "output": f"Starting {task_type.lower()} task",
            "status": task_type  # Add explicit status field
        })
        
        try:
            # Execute the task
            result = original_execute_sync(self, *args, **kwargs)
            
            # Send completion status
            sync_send_status({
                "agent": agent_name,
                "task": "Done",  # Send Done directly instead of Completed
                "output": f"Completed {task_type.lower()} task",
                "status": "Done"  # Add explicit status field
            })
            
            return result
        except Exception as e:
            # Send error status
            sync_send_status({
                "agent": agent_name,
                "task": "Error",
                "output": f"Error in {task_type.lower()} task: {str(e)}",
                "status": "Error"  # Add explicit status field
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