import streamlit as st
import websockets
import asyncio
import json
import aiohttp
from datetime import datetime
import threading
from queue import Queue
import time
import logging
import streamlit.logger

# Configure logging
logger = streamlit.logger.get_logger(__name__)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ws_connection" not in st.session_state:
    st.session_state.ws_connection = None
if "connected" not in st.session_state:
    st.session_state.connected = False
if "message_queue" not in st.session_state:
    st.session_state.message_queue = Queue()
if "processing" not in st.session_state:
    st.session_state.processing = False
if "last_update" not in st.session_state:
    st.session_state.last_update = None
if "backend_url" not in st.session_state:
    st.session_state.backend_url = "localhost:8888"
if "completed_agents" not in st.session_state:
    st.session_state.completed_agents = set()

# Streamlit UI configuration
st.set_page_config(page_title="CrewAI Content Creation", page_icon="🤖", layout="wide")

# Custom CSS for modern styling with theme support
st.markdown(
    """
    <style>
        /* Modern, professional color scheme */
        :root {
            --primary-color: #1a73e8;
            --secondary-color: #4285f4;
            --success-color: #0f9d58;
            --warning-color: #f4b400;
            --error-color: #db4437;
            --bg-color: #ffffff;
            --text-color: #202124;
            --border-color: #dadce0;
            --content-bg: #f8f9fa;
        }
        
        /* Dark mode */
        @media (prefers-color-scheme: dark) {
            :root {
                --primary-color: #8ab4f8;
                --secondary-color: #669df6;
                --success-color: #81c995;
                --warning-color: #fdd663;
                --error-color: #f28b82;
                --bg-color: #202124;
                --text-color: #e8eaed;
                --border-color: #3c4043;
                --content-bg: #292a2d;
            }
        }
        
        /* Main container styling */
        .main {
            padding: 1rem;
            color: var(--text-color);
        }
        
        /* Typography */
        h1, h2, h3 {
            color: var(--text-color);
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
            margin: 0.5rem 0;
            padding: 0;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            font-size: 1.1rem;
            font-weight: 600;
            margin: 0.5rem 0;
            background-color: var(--background-color) !important;
            border: 1px solid var(--secondary-background-color) !important;
        }
        
        /* Content card styling */
        .content-card {
            background-color: var(--content-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }

        .content-card .metadata {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
            color: var(--text-color);
            opacity: 0.8;
            margin-bottom: 1rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
        }

        .content-card .content {
            font-size: 1rem;
            line-height: 1.6;
            color: var(--text-color);
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        /* Status message styling */
        .status-updates {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .status-message {
            padding: 0.4rem 0.8rem;
            border-radius: 16px;
            font-size: 0.85rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: white;
        }

        .status-message.system { background-color: var(--primary-color); }
        .status-message.research { background-color: var(--success-color); }
        .status-message.writer { background-color: var(--warning-color); }
        .status-message.editor { background-color: var(--error-color); }

        /* Agent section styling */
        .agent-section {
            background-color: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
        }

        .agent-section h3 {
            color: var(--primary-color);
            font-size: 1.2rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* Phase indicators */
        .phase-indicator {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin: 1rem 0;
            padding: 1rem;
            background-color: var(--content-bg);
            border-radius: 8px;
        }

        .phase-step {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--text-color);
            opacity: 0.6;
        }

        .phase-step.active {
            opacity: 1;
            color: var(--primary-color);
        }

        /* Content sections */
        .research-content, .draft-content, .final-content {
            margin-top: 1rem;
        }

        .content-header {
            font-weight: 500;
            color: var(--text-color);
            margin-bottom: 0.5rem;
        }

        /* Sidebar styling */
        .css-1d391kg {
            padding: 1rem;
        }

        /* Input field styling */
        .stTextInput > div > div > input {
            border-radius: 6px;
            border: 1px solid var(--secondary-background-color);
            padding: 0.5rem 0.75rem;
            background-color: var(--background-color);
            color: var(--text-color);
        }
        
        /* Button styling */
        .stButton > button {
            border-radius: 6px;
            padding: 0.5rem 1.5rem;
            background-color: var(--accent-color);
            color: white;
            border: none;
            transition: all 0.2s ease;
            font-weight: 500;
        }
        
        .stButton > button:hover {
            background-color: #81A1C1;
            transform: translateY(-1px);
        }

        /* Status message styling */
        .stAlert {
            padding: 0.5rem 1rem;
            margin: 0.5rem 0;
        }

        /* Remove extra padding from containers */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }

        /* Streamlit default element spacing */
        .element-container {
            margin-bottom: 0.5rem;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# Create placeholder for messages
messages_placeholder = st.empty()

# Create a placeholder for status messages
status_placeholder = st.empty()

# Sidebar for configuration
with st.sidebar:
    st.title("⚙️ Configuration")
    backend_url = st.text_input(
        "Backend URL",
        value=st.session_state.backend_url,
        help="Enter the backend server URL (without protocol)",
        key="backend_url_input"
    )
    # Update the session state when input changes
    st.session_state.backend_url = backend_url
    
    if st.button("Connect", type="primary"):
        st.session_state.connected = True
        logger.info(f"Connected to backend at {backend_url}")

# Main content area
st.title("🤖 CrewAI Content Creation")


def websocket_receiver(uri, queue):
    """Background thread function for WebSocket connection."""
    
    def run_async_loop():
        async def connect_and_receive():
            connection_count = 0
            while True:  # Keep trying to reconnect
                try:
                    connection_count += 1
                    logger.info(f"[CONNECTION #{connection_count}] Attempting to connect to WebSocket at {uri}")
                    async with websockets.connect(uri) as websocket:
                        st.session_state.ws_connection = websocket
                        logger.info(f"[CONNECTION #{connection_count}] WebSocket connection established")
                        
                        while True:
                            try:
                                message = await websocket.recv()
                                data = json.loads(message)
                                logger.info(f"[CONNECTION #{connection_count}] Received message: {data}")
                                
                                # Process both status and content messages
                                queue.put(data)
                                st.session_state.processing = True
                                st.session_state.last_update = time.time()
                                
                            except websockets.exceptions.ConnectionClosed:
                                logger.warning(f"[CONNECTION #{connection_count}] WebSocket connection closed, attempting to reconnect...")
                                break
                            except Exception as e:
                                logger.error(f"[CONNECTION #{connection_count}] Error receiving message: {str(e)}")
                                break
                                
                except Exception as e:
                    logger.error(f"[CONNECTION #{connection_count}] WebSocket connection error: {str(e)}")
                    await asyncio.sleep(2)  # Wait before retrying
                    continue
                    
                finally:
                    st.session_state.ws_connection = None
                    logger.info(f"[CONNECTION #{connection_count}] Connection cleanup complete")

        # Create and run a new event loop in this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(connect_and_receive())

    # Start the async loop in a new thread
    thread = threading.Thread(target=run_async_loop, daemon=True)
    thread.start()
    return thread


async def send_topic_async(backend_url, topic):
    """Send topic to backend API."""
    try:
        logger.info(f"Sending topic '{topic}' to backend")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{backend_url}/start", json={"topic": topic}
            ) as response:
                result = await response.json()
                logger.info(f"Backend response: {result}")
                return result
    except Exception as e:
        logger.error(f"Failed to send topic: {str(e)}")
        st.error(f"Failed to send topic: {str(e)}")
        return None


def send_topic(backend_url, topic):
    """Synchronous wrapper for send_topic_async."""
    return asyncio.run(send_topic_async(backend_url, topic))


# Input area
if st.session_state.connected:
    topic = st.text_input(
        "Enter your topic",
        placeholder="e.g., The Future of AI in Healthcare",
        key="topic_input",
    )

    if st.button("Generate Content", key="generate_btn"):
        if topic:
            logger.info(f"Starting content generation for topic: {topic}")
            # Clear previous messages and state
            st.session_state.messages = []
            st.session_state.completed_agents = set()
            st.session_state.processing = True
            st.session_state.last_update = time.time()

            # Start WebSocket connection in a background thread
            ws_uri = f"ws://{backend_url}/ws"
            st.session_state.receiver_thread = websocket_receiver(ws_uri, st.session_state.message_queue)
            logger.info("WebSocket receiver thread started")

            # Send topic to backend
            response = send_topic(backend_url, topic)
            if response:
                st.success("Content generation started!")
                logger.info("Content generation process initiated successfully")


def update_messages():
    """Update and display messages."""
    messages_processed = False
    
    logger.info(f"[UI] Current message queue size: {st.session_state.message_queue.qsize()}")
    logger.info(f"[UI] Current session state messages count: {len(st.session_state.messages)}")
    
    try:
        while not st.session_state.message_queue.empty():
            try:
                data = st.session_state.message_queue.get_nowait()
                logger.info(f"[UI] Processing message: {json.dumps(data, indent=2)}")
                
                # Ensure all required fields exist with defaults
                msg_type = data.get("type", "status")
                output = data.get("output", "")
                agent = data.get("agent", "System")
                task = data.get("task", "Unknown")

                # Track completed agents
                if task == "Done" or task == "Completed":
                    st.session_state.completed_agents.add(agent)
                    logger.info(f"[UI] Agent {agent} completed. Current completed agents: {st.session_state.completed_agents}")

                # Skip empty messages
                if not output:
                    logger.warning("[UI] Skipping empty message")
                    continue

                message_entry = {
                    "timestamp": data.get("timestamp", datetime.now().strftime("%H:%M:%S")),
                    "agent": agent,
                    "task": task,
                    "output": output,
                    "type": msg_type
                }
                
                # Add message to session state
                if "messages" not in st.session_state:
                    st.session_state.messages = []
                st.session_state.messages.append(message_entry)
                messages_processed = True
                logger.info(f"[UI] Added message to state. Current count: {len(st.session_state.messages)}")
                
            except Exception as e:
                logger.error(f"[UI] Error processing message: {str(e)}")
                continue
    except Exception as e:
        logger.error(f"[UI] Error in message processing loop: {str(e)}")

    with messages_placeholder.container():
        if st.session_state.messages:
            # Group messages by agent
            agent_messages = {}
            for msg in st.session_state.messages:
                agent = msg.get("agent", "System")
                if agent not in agent_messages:
                    agent_messages[agent] = []
                agent_messages[agent].append(msg)
            
            # Display system messages first
            if "System" in agent_messages:
                with st.expander("System Status", expanded=True):
                    st.markdown('<div class="status-updates">', unsafe_allow_html=True)
                    for msg in agent_messages["System"]:
                        st.markdown(
                            f"""
                            <div class="status-message system">
                                <span>{msg.get('timestamp', '')}</span>
                                <span>•</span>
                                <span>{msg.get('output', '')}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Display agent content in sequence
            for agent_name in ["Research Agent", "Writer Agent", "Editor Agent"]:
                if agent_name in agent_messages:
                    messages = agent_messages[agent_name]
                    with st.expander(f"{agent_name} {'✓' if agent_name in st.session_state.completed_agents else ''}", expanded=True):
                        st.markdown(f'<div class="agent-section">', unsafe_allow_html=True)
                        
                        # Show content first (reversed to show latest on top)
                        content_messages = [msg for msg in messages if msg.get("type") == "content"]
                        if content_messages:
                            for msg in reversed(content_messages):
                                st.markdown(
                                    f"""
                                    <div class="content-card">
                                        <div class="metadata">
                                            <span>{msg.get('timestamp', '')}</span>
                                            <span>•</span>
                                            <span>{agent_name}</span>
                                            <span>•</span>
                                            <span>{msg.get('task', 'Unknown')}</span>
                                        </div>
                                        <div class="content">
                                            {msg.get('output', '').replace('\\n', '<br>')}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                        
                        # Show status updates below content
                        status_messages = [msg for msg in messages if msg.get("type") == "status"]
                        if status_messages:
                            st.markdown('<div class="status-updates">', unsafe_allow_html=True)
                            for msg in status_messages:
                                agent_class = agent_name.lower().split()[0]
                                st.markdown(
                                    f"""
                                    <div class="status-message {agent_class}">
                                        <span>{msg.get('timestamp', '')}</span>
                                        <span>•</span>
                                        <span>{msg.get('output', '')}</span>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)

    # Update processing state based on completed agents
    expected_agents = {"System", "Research Agent", "Writer Agent", "Editor Agent"}
    if st.session_state.completed_agents >= expected_agents:
        st.session_state.processing = False
        logger.info("[UI] All agents completed their tasks")
    
    return messages_processed


# Auto-refresh mechanism
if st.session_state.connected:
    messages_processed = update_messages()

    # Update status message
    with status_placeholder.container():
        if st.session_state.processing:
            st.info("⏳ Generating content...", icon="ℹ️")
            time.sleep(0.1)
            st.rerun()
        elif st.session_state.messages:
            st.success("✅ Content generation completed!", icon="✅")

# Footer with modern styling
st.markdown("---")
st.markdown(
    """
    <div style="
        text-align: center;
        padding: 1rem;
        color: var(--text-color);
        font-size: 0.9rem;
    ">
        Made with ❤️ using CrewAI, Streamlit, and WebSocket
    </div>
    """,
    unsafe_allow_html=True,
)
