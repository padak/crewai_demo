import streamlit as st
import requests
import json
import threading
from websocket import create_connection, WebSocketException
from streamlit_autorefresh import st_autorefresh
import time

# Global variable to store messages from the WebSocket listener.
global_messages = []

def websocket_listener():
    """
    Connect to the WebSocket server and append incoming status updates
    into the global_messages list.
    """
    ws_url = "ws://localhost:8888/ws"
    try:
        ws = create_connection(ws_url)
    except Exception as e:
        # If connection fails, record the error and exit the thread.
        global_messages.append({"error": f"WebSocket connection failed: {str(e)}"})
        return

    while True:
        try:
            result = ws.recv()
            data = json.loads(result)
            global_messages.append(data)
        except WebSocketException as we:
            global_messages.append({"error": f"WebSocket error: {str(we)}"})
            break  # Exit the loop if there is a connection error.
        except Exception as e:
            global_messages.append({"error": str(e)})
            break
        # Sleep briefly to avoid busy-looping.
        time.sleep(0.1)

# Initialize session state in the main thread.
if "ws_listener_started" not in st.session_state:
    st.session_state.ws_listener_started = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# Start the WebSocket listener thread if not already started.
if not st.session_state.ws_listener_started:
    threading.Thread(target=websocket_listener, daemon=True).start()
    st.session_state.ws_listener_started = True

# Update session state messages from the global_messages list.
st.session_state.messages = global_messages

st.title("Content Creation Pipeline Monitor")

# Input box for the topic.
topic = st.text_input("Enter topic", "The Future of AI in Healthcare")

# Button to trigger content creation.
if st.button("Start Content Creation"):
    # Clear previous messages
    global_messages.clear()
    st.session_state.messages = []
    
    # Show spinner while waiting for the backend to return the final content.
    with st.spinner("Processing your request, please wait..."):
        try:
            response = requests.post("http://localhost:8000/create-content", json={"topic": topic})
            if response.ok:
                final_content = response.json().get("content", "")
                st.success("Final Content:")
                st.write(final_content)
            else:
                st.error("Error: " + str(response.text))
        except Exception as e:
            st.error("Request failed: " + str(e))

# Display Agent Progress
st.header("Agent Progress")

# Define the expected agents
agents = ["Research Agent", "Writer Agent", "Editor Agent"]

for agent in agents:
    st.subheader(agent)
    # Filter messages for this agent
    agent_messages = [msg for msg in st.session_state.messages if msg.get("agent") == agent]
    if agent_messages:
        # Display the latest status update
        latest_message = agent_messages[-1]
        st.markdown(f"**Current Status:** {latest_message.get('status', 'N/A')}")
        st.markdown(f"**Latest Output:** {latest_message.get('output', '')}")
        with st.expander(f"Full Update Log for {agent}"):
            st.write(agent_messages)
    else:
        st.write("No updates yet.")

# Display any system logs (messages without an agent field, such as connection errors)
system_messages = [msg for msg in st.session_state.messages if "agent" not in msg]
if system_messages:
    st.header("System Logs")
    st.write(system_messages)

# Auto-refresh the page every 2 seconds to update the status messages.
st_autorefresh(interval=2000, key="autorefresh")
