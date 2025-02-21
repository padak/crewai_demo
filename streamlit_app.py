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
    st.session_state.backend_url = "localhost:8000"

# Streamlit UI configuration
st.set_page_config(page_title="CrewAI Content Creation", page_icon="🤖", layout="wide")

# Custom CSS for modern styling with theme support
st.markdown(
    """
    <style>
        /* Modern color scheme with theme support */
        :root {
            --primary-color: var(--text-color);
            --background-color: var(--background-color);
            --accent-color: #5E81AC;
            --success-color: #A3BE8C;
            --warning-color: #EBCB8B;
            --error-color: #BF616A;
            --text-color: var(--text-color);
            --card-bg-color: var(--background-color);
            --card-border-color: var(--secondary-background-color);
            --code-bg-color: var(--secondary-background-color);
            --status-bg-color: var(--secondary-background-color);
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
            background-color: var(--background-color);
            border: 1px solid var(--secondary-background-color);
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }

        /* Code block styling */
        .code-block {
            background-color: var(--secondary-background-color);
            border-radius: 6px;
            padding: 0.75rem;
            font-family: 'SF Mono', monospace;
            font-size: 0.9rem;
            line-height: 1.4;
            white-space: pre-wrap;
            margin-top: 0.5rem;
        }

        /* Metadata styling */
        .metadata {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            margin-bottom: 0.5rem;
            color: var(--text-color);
            opacity: 0.8;
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

    async def connect_and_receive():
        try:
            logger.info(f"Attempting to connect to WebSocket at {uri}")
            async with websockets.connect(uri) as websocket:
                st.session_state.ws_connection = websocket
                logger.info("WebSocket connection established")
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        logger.info(f"Received message: {data}")
                        # Process both status and content messages
                        queue.put(data)
                        st.session_state.processing = True
                        st.session_state.last_update = time.time()
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("WebSocket connection closed")
                        break
                    except Exception as e:
                        logger.error(f"Error receiving message: {str(e)}")
                        break
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
        finally:
            st.session_state.processing = False
            logger.info("WebSocket receiver stopped")

    asyncio.run(connect_and_receive())


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
            # Clear previous messages
            st.session_state.messages = []
            st.session_state.processing = True
            st.session_state.last_update = time.time()

            # Start WebSocket connection in a background thread
            ws_uri = f"ws://{backend_url}/ws"
            receiver_thread = threading.Thread(
                target=websocket_receiver,
                args=(ws_uri, st.session_state.message_queue),
                daemon=True,
            )
            receiver_thread.start()
            logger.info("WebSocket receiver thread started")

            # Send topic to backend
            response = send_topic(backend_url, topic)
            if response:
                st.success("Content generation started!")
                logger.info("Content generation process initiated successfully")


def update_messages():
    """Update and display messages."""
    messages_processed = False
    while not st.session_state.message_queue.empty():
        data = st.session_state.message_queue.get()
        output = data.get("output", "")
        agent = data.get("agent", "System")
        task = data.get("task", "Unknown")

        if output and not output.startswith("Starting") and not output.startswith("Completed"):
            message_entry = {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "agent": agent,
                "task": task,
                "output": output,
            }
            st.session_state.messages.append(message_entry)
            messages_processed = True
            logger.info(f"Processed content message: {message_entry}")

    with messages_placeholder.container():
        if st.session_state.messages:
            st.subheader("Generated Content")
            
            # Group messages by agent
            agent_messages = {}
            for msg in st.session_state.messages:
                if msg["agent"] not in agent_messages:
                    agent_messages[msg["agent"]] = []
                agent_messages[msg["agent"]].append(msg)
            
            # Display content by agent
            for agent, messages in agent_messages.items():
                with st.expander(f"{agent}", expanded=True):
                    for msg in messages:
                        st.markdown(
                            f"""
                            <div class="content-card">
                                <div class="metadata">
                                    <span>{msg['timestamp']}</span>
                                    <span>•</span>
                                    <span style="color: var(--accent-color)">{msg['task']}</span>
                                </div>
                                <div class="code-block">{msg['output']}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

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
