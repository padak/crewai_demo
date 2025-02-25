# CrewAI Content Orchestrator with HITL

This project demonstrates how to use CrewAI with Human-in-the-Loop (HITL) capabilities for content generation. The system allows for asynchronous content creation with human feedback integration.

## What We've Done

We've implemented a content generation system using CrewAI's recommended patterns:

1. Created a `ContentCreationCrew` class with the `@CrewBase` decorator
2. Defined agents using the `@agent` decorator for research, writing, and editing
3. Defined tasks using the `@task` decorator with proper input handling
4. Defined crews using the `@crew` decorator for sequential processing
5. Implemented a FastAPI wrapper (`api_wrapper.py`) for asynchronous job processing
6. Added HITL functionality to allow human feedback on generated content
7. Created webhook notifications for real-time status updates
8. Unified client interface in a single `api_client.py` file

The application now follows CrewAI's recommended structure and terminology, making it more maintainable and aligned with best practices.

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.streamlit/secrets.toml` file with your OpenRouter API key:

   ```toml
   OPENROUTER_API_KEY = "your-api-key-here"
   ```

## Running the Service

1. Start the API wrapper:

   ```bash
   source .venv/bin/activate
   export DATA_APP_ENTRYPOINT="orchestrator_service.py"
   uvicorn api_wrapper:app --host 0.0.0.0 --port 8888 \
     --timeout-keep-alive 300 \
     --timeout-graceful-shutdown 300 --loop asyncio
   ```

2. (Optional) Start the webhook receiver for HITL workflows:

   ```bash
   source .venv/bin/activate
   python webhook_receiver.py --host 0.0.0.0 --port 8889
   ```

## Using the Unified Client

The `api_client.py` script provides a unified interface for interacting with the API wrapper. It supports both direct content generation and Human-in-the-Loop (HITL) workflows.

### Direct Content Generation

For direct content generation without human approval:

```bash
python api_client.py --topic "Artificial Intelligence" --mode direct --wait
```

This will generate content on the specified topic and wait for the result.

### Human-in-the-Loop (HITL) Workflow

For content generation with human approval:

```bash
python api_client.py --topic "Quantum Computing" --mode hitl --webhook http://localhost:8889/webhook
```

This will start a content generation job and send webhook notifications when the content is ready for review.

When the content is ready, you can either approve it or provide feedback:

```bash
# To approve the content
python api_client.py --job-id "your-job-id" --approve

# To provide feedback
python api_client.py --job-id "your-job-id" --feedback "Please add more examples of practical applications"
```

For detailed information about the HITL workflow, see [HITL_WORKFLOW.md](HITL_WORKFLOW.md).

## Remote Deployment Usage

When the service is deployed remotely (e.g., on a cloud platform or server), you need to adjust your client commands to account for potential timeout issues and network constraints.

### Connecting to a Remote Server

Specify the remote server URL with the `--url` parameter:

```bash
python api_client.py --topic "Artificial Intelligence" --mode direct --url https://your-remote-server.com
```

### Handling Timeouts with Asynchronous Processing

When working with remote deployments, **avoid using the `--wait` flag** for long-running operations as it may cause timeout errors (502 Bad Gateway). Instead, use the asynchronous approach:

```bash
# Start a job asynchronously
python api_client.py --topic "Artificial Intelligence" --mode direct --url https://your-remote-server.com

# Then check the status later using the job ID
curl https://your-remote-server.com/job/your-job-id
```

### Example with Real Remote Deployment

```bash
# Start a content generation job
python api_client.py --topic "Artificial Intelligence" --mode direct --url https://flask-550.hub.canary-orion.keboola.dev

# The command will return a job ID, which you can use to check status
curl https://flask-550.hub.canary-orion.keboola.dev/job/8cdec218-a0bc-44ab-b4e3-133ffa778038
```

### Setting Up a Local Webhook Receiver

For remote deployments, you may need to set up a publicly accessible webhook endpoint or use a service like ngrok to expose your local webhook receiver:

```bash
# Start the webhook receiver locally
python webhook_receiver.py --host 0.0.0.0 --port 8889

# In another terminal, use ngrok to expose it
ngrok http 8889

# Then use the ngrok URL as your webhook
python api_client.py --topic "Climate Change" --mode hitl --url https://your-remote-server.com --webhook https://your-ngrok-url.ngrok.io/webhook
```

## API Endpoints

### Starting a Content Creation Job

```bash
curl -X POST "http://localhost:8888/kickoff" \
  -H "Content-Type: application/json" \
  -d '{
    "crew": "ContentCreationCrew",
    "inputs": {
      "topic": "Your Topic Here",
      "require_approval": false  # Optional, defaults to true
    },
    "webhook_url": "http://localhost:8889/webhook"
  }'
```

### Checking Job Status

```bash
curl "http://localhost:8888/job/{job_id}"
```

### Providing Feedback

```bash
# Approve content
curl -X POST "http://localhost:8888/job/{job_id}/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "Looks great!",
    "approved": true
  }'

# Request revisions
curl -X POST "http://localhost:8888/job/{job_id}/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "Please make the content more concise and add more examples.",
    "approved": false
  }'
```

## How the Application Works

### Core Components

1. **`orchestrator_service.py`**: Contains the CrewAI implementation with:
   - Agent definitions for research, writing, and editing
   - Task definitions with proper input handling
   - Crew definitions for sequential processing
   - API-compatible functions for HITL workflow

2. **`api_wrapper.py`**: FastAPI wrapper that provides:
   - Asynchronous job processing
   - Job status tracking
   - Webhook notifications
   - Feedback handling

3. **`api_client.py`**: Unified client interface that provides:
   - Direct content generation without human approval
   - Human-in-the-Loop workflow with feedback
   - Synchronous and asynchronous operation modes
   - Command-line interface with various options

4. **`webhook_receiver.py`**: Simple webhook receiver for testing

### Workflow

1. Client sends a request to `/kickoff` with a topic
2. The system processes the request asynchronously
3. If `require_approval` is `true` (default):
   - When content is ready, the job status changes to "pending_approval"
   - A webhook notification is sent (if configured)
   - Human reviews the content and provides feedback
   - If approved, the job is marked as completed
   - If not approved, the content is regenerated with the feedback
4. If `require_approval` is `false`:
   - When content is ready, the job status changes to "completed"
   - A webhook notification is sent (if configured)
   - No human review is required
5. Final content is available through the job status endpoint

## Understanding Client Options

The unified client (`api_client.py`) provides several options to control how content is generated:

### Mode Options

- **`--mode direct`**: Generate content without human approval
- **`--mode hitl`**: Generate content with human review and feedback

### Processing Options

- **`--wait`**: Wait for completion instead of polling (direct mode only)
- **`--async`**: Use asynchronous processing for better performance (hitl mode only)

### HITL Options

- **`--approve`**: Automatically approve content without providing feedback
- **`--feedback TEXT`**: Provide specific feedback for content revision

### Other Options

- **`--topic TEXT`**: Specify the content topic (required)
- **`--url TEXT`**: API endpoint URL (defaults to localhost:8888)
- **`--webhook TEXT`**: URL for webhook notifications

## Project Structure

```
crewai_demo/
├── .env                    # Environment variables
├── .env.sample             # Sample environment variables
├── .streamlit/             # Streamlit configuration
│   └── secrets.toml        # API keys and secrets
├── agents/                 # Agent definitions
├── api_client.py           # Unified client interface
├── api_wrapper.py          # FastAPI wrapper for CrewAI
├── HITL_IMPLEMENTATION.md  # HITL implementation details
├── orchestrator_service.py # CrewAI implementation
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── tasks/                  # Task definitions
└── webhook_receiver.py     # Simple webhook receiver for testing
```

## Current Issues and TODO

### Current Issues

We're currently facing an error when running the application:

```
'function' object has no attribute 'get'
```

This error occurs in the `process_job_in_background` function in `api_wrapper.py` when trying to process the result from `crew.kickoff()`.

### What We've Tried

1. Updated the `process_job_in_background` function to handle different result types:
   - Added conversion of TaskOutput objects to dictionaries
   - Added handling for string results
   - Added proper error handling

2. Updated the `create_content_with_hitl` function to use the crew's `kickoff` method correctly:
   - Simplified the input handling
   - Removed manual task input setting
   - Used the `kickoff(inputs=inputs)` pattern as recommended in the CrewAI docs

3. Updated task methods to properly handle inputs:
   - Added `inputs = inputs or {}` pattern to all task methods
   - Used `inputs.get()` to extract values with defaults
   - Added the `human_input` parameter as per the CrewAI docs

### Next Steps

1. Debug the `'function' object has no attribute 'get'` error:
   - Add more detailed logging to identify exactly where the error occurs
   - Check if the crew methods are being called correctly
   - Verify that the inputs are being passed correctly to the tasks

2. Consider creating YAML configuration files for agents and tasks as recommended in the CrewAI docs:
   - Create `config/agents.yaml` and `config/tasks.yaml`
   - Update the code to use these configuration files

3. Implement proper error handling for missing configuration files:
   - Add fallback mechanisms when configuration files are not found
   - Provide clear error messages for missing configurations

4. Add comprehensive testing:
   - Create unit tests for the core functionality
   - Add integration tests for the API endpoints
   - Test the HITL workflow end-to-end

## Docker Deployment

Build and run the Docker container:

```bash
docker build -t crewai-hitl .
docker run -p 8888:8888 -v $(pwd)/.streamlit:/app/.streamlit crewai-hitl
```
