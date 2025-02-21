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
    "ws_url": "ws://localhost:8888/ws",
    "initialized": False,
    "topic": None,
    "websocket": None,
    "message_queue": asyncio.Queue()
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
    logger.info(
        f"STATUS DEBUG - Status normalized from '{message.get('task')}' to '{status}'"
    )

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
            "role": agent_name,  # Use full agent name as role for UI
        },
    }

    logger.info(
        f"STATUS DEBUG - Final message to send: {json.dumps(enhanced_message, indent=2)}"
    )

    # Add message to queue for sending
    await config["message_queue"].put(enhanced_message)


def sync_send_status(message):
    """Synchronous wrapper for send_status_update."""
    try:
        asyncio.run(send_status_update(message))
    except Exception as e:
        logger.error(f"Failed to queue status update: {str(e)}")


async def websocket_sender():
    """Background task to send messages via WebSocket."""
    while True:
        try:
            if not config["websocket"]:
                config["websocket"] = await websockets.connect(config["ws_url"])
                logger.info("WebSocket connection established")

            # Get message from queue
            message = await config["message_queue"].get()
            
            try:
                await config["websocket"].send(json.dumps(message))
                logger.info(f"Successfully sent message for agent {message.get('agent')} with status {message.get('status')}")
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed, reconnecting...")
                config["websocket"] = None
                # Put the message back in the queue
                await config["message_queue"].put(message)
            except Exception as e:
                logger.error(f"Error sending message: {str(e)}")
                # Put the message back in the queue
                await config["message_queue"].put(message)

        except Exception as e:
            logger.error(f"Error in websocket sender: {str(e)}")
            await asyncio.sleep(1)  # Wait before retrying


def get_task_info(task):
    """Extract task and agent information."""
    # Map agent roles to UI-expected names
    role_to_name = {
        "Research Analyst": "Research Agent",
        "Content Writer": "Writer Agent",
        "Content Editor": "Editor Agent",
    }

    # Get the agent's role
    agent_role = task.agent.role if hasattr(task.agent, "role") else "Unknown"
    # Map to UI-expected name
    agent_name = role_to_name.get(agent_role, agent_role)

    description = str(getattr(task, "description", ""))

    # Determine task type based on agent name and description
    if "research" in agent_name.lower():
        task_type = "Researching"
    elif "writer" in agent_name.lower() or "content writer" in agent_role.lower():
        task_type = "Writing"
    elif "editor" in agent_name.lower() or "edit" in description.lower():
        task_type = "Editing"
    else:
        task_type = "Processing"

    logger.info(
        f"TASK DEBUG - Agent '{agent_name}' (role: '{agent_role}') resolved task type: '{task_type}'"
    )
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
        sync_send_status(
            {
                "agent": agent_name,
                "task": task_type,
                "output": f"Starting {task_type.lower()} task",
                "status": task_type,
                "type": "status",
            }
        )

        try:
            # Execute the task
            result = await original_execute_async(self, *args, **kwargs)

            logger.info(f"EXECUTION DEBUG - Completed async execution for {agent_name}")

            # Send the actual content first
            if result:
                content_message = {
                    "agent": agent_name,
                    "task": task_type,
                    "output": str(result),
                    "type": "content",
                    "timestamp": datetime.now().isoformat()
                }
                sync_send_status(content_message)
                logger.info(f"CONTENT DEBUG - Sent content for {agent_name}: {str(result)[:100]}...")

            # Then send completion status
            sync_send_status(
                {
                    "agent": agent_name,
                    "task": "Done",
                    "output": f"Completed {task_type.lower()} task",
                    "status": "Done",
                    "type": "status",
                }
            )

            return result
        except Exception as e:
            logger.error(
                f"EXECUTION DEBUG - Error in async execution for {agent_name}: {str(e)}"
            )
            # Send error status
            sync_send_status(
                {
                    "agent": agent_name,
                    "task": "Error",
                    "output": f"Error in {task_type.lower()} task: {str(e)}",
                    "status": "Error",
                    "type": "status",
                }
            )
            raise

    def monitored_execute_sync(self, *args, **kwargs):
        """Monitored version of sync task execution."""
        if not config["initialized"]:
            return original_execute_sync(self, *args, **kwargs)

        agent_name, task_type = get_task_info(self)

        # Send start status
        sync_send_status(
            {
                "agent": agent_name,
                "task": task_type,
                "output": f"Starting {task_type.lower()} task",
                "status": task_type,
                "type": "status",
            }
        )

        try:
            # Execute the task
            result = original_execute_sync(self, *args, **kwargs)

            # Send the actual content first
            if result:
                content_message = {
                    "agent": agent_name,
                    "task": task_type,
                    "output": str(result),
                    "type": "content",
                    "timestamp": datetime.now().isoformat()
                }
                sync_send_status(content_message)
                logger.info(f"CONTENT DEBUG - Sent content for {agent_name}: {str(result)[:100]}...")

            # Then send completion status
            sync_send_status(
                {
                    "agent": agent_name,
                    "task": "Done",
                    "output": f"Completed {task_type.lower()} task",
                    "status": "Done",
                    "type": "status",
                }
            )

            return result
        except Exception as e:
            # Send error status
            sync_send_status(
                {
                    "agent": agent_name,
                    "task": "Error",
                    "output": f"Error in {task_type.lower()} task: {str(e)}",
                    "status": "Error",
                    "type": "status",
                }
            )
            raise

    def monitored_crew_kickoff(self, *args, **kwargs):
        """Monitored version of Crew kickoff."""
        if not config["initialized"]:
            return original_crew_kickoff(self, *args, **kwargs)

        # Send start status
        sync_send_status(
            {
                "agent": "System",
                "task": "Starting",
                "output": f"Beginning content creation for topic: {config['topic']}",
                "type": "status"
            }
        )

        try:
            # Execute the crew tasks
            result = original_crew_kickoff(self, *args, **kwargs)

            # Send completion status
            sync_send_status(
                {
                    "agent": "System",
                    "task": "Completed",
                    "output": "Content creation process finished successfully",
                    "type": "status"
                }
            )

            return result
        except Exception as e:
            # Send error status
            sync_send_status(
                {
                    "agent": "System",
                    "task": "Error",
                    "output": f"Error in content creation: {str(e)}",
                    "type": "status"
                }
            )
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

    # Create and run event loop in a separate thread
    def run_event_loop():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(websocket_sender())
        except Exception as e:
            logger.error(f"Error in event loop: {str(e)}")

    # Start event loop thread
    import threading
    event_loop_thread = threading.Thread(target=run_event_loop, daemon=True)
    event_loop_thread.start()

    # Patch CrewAI classes
    patch_crewai()

    # Mark as initialized
    config["initialized"] = True

    # Send initial connection status
    sync_send_status(
        {
            "agent": "System",
            "task": "Connection",
            "output": "Monitoring system initialized",
            "type": "status"
        }
    )

    logger.info("CrewAI monitoring initialized successfully")
