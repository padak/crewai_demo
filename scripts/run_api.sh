#!/bin/bash
# Script to run the API wrapper with the new project structure

# shellcheck disable=SC1091
# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# shellcheck disable=SC1091
if [ -f ".env" ]; then
    source .env
fi

# Set environment variables
export DATA_APP_ENTRYPOINT="crewai_app/orchestrator.py"

# Run the API wrapper
uvicorn api_wrapper.api_wrapper:app --host 0.0.0.0 --port 8888 \
  --timeout-keep-alive 300 \
  --timeout-graceful-shutdown 300 \
  --reload

# Note: The --reload flag is for development only
# Remove it for production deployments 