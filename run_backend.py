#!/usr/bin/env python3
"""
Entry point for the CrewAI Content Creation backend server.
Run this script to start the FastAPI server on port 8888.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import the server starter
from backend.app.main import start_server

if __name__ == "__main__":
    # Ensure we're in the project root directory
    os.chdir(project_root)
    
    print("Starting CrewAI Content Creation backend server...")
    print("Server will be available at: http://localhost:8888")
    print("WebSocket endpoint at: ws://localhost:8888/ws")
    print("API documentation at: http://localhost:8888/docs")
    
    # Start the server
    start_server() 