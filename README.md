# CrewAI Content Orchestrator with HITL

This project demonstrates how to use CrewAI with Human-in-the-Loop (HITL) capabilities for content generation.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.streamlit/secrets.toml` file with your OpenRouter API key:
   ```toml
   OPENROUTER_API_KEY = "your-api-key-here"
   ```

## Running the Service

1. Start the API wrapper:
   ```bash
   export DATA_APP_ENTRYPOINT="orchestrator_service.py"
   uvicorn api_wrapper:app --host 0.0.0.0 --port 8888 \
     --proxy-headers --forwarded-allow-ips "*" \
     --timeout-keep-alive 300 \
     --timeout-graceful-shutdown 300 --loop asyncio \
     --workers 1 --limit-concurrency 1000 \
     --backlog 2048 --no-server-header --no-date-header
   ```

2. (Optional) Start the webhook receiver for testing:
   ```bash
   python webhook_receiver.py --port 8889
   ```

## Testing the HITL Workflow

You can test the HITL workflow using the provided test client:

```bash
# Start a job and provide feedback
python hitl_test_client.py --topic "Climate Change Solutions"

# Start a job and approve the content
python hitl_test_client.py --topic "Space Exploration" --approve

# Start a job with custom feedback
python hitl_test_client.py --topic "Quantum Computing" --feedback "Please focus more on practical applications and less on theory."
```

## API Endpoints

### Starting a Content Creation Job

```bash
curl -X POST "http://localhost:8888/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "function": "create_content_with_hitl",
    "args": ["Your Topic Here"],
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

### Listing All Jobs

```bash
curl "http://localhost:8888/jobs"
```

## How the HITL Workflow Works

1. **Initial Request**: Client makes a request to `/invoke` with the `create_content_with_hitl` function.

2. **Background Processing**: The system processes the request asynchronously.

3. **Pending Approval**: When content is ready for review, the job status changes to `pending_approval`.

4. **Webhook Notification**: If a webhook URL was provided, a notification is sent.

5. **Human Review**: A human reviews the content and provides feedback.

6. **Feedback Processing**:
   - If approved, the job is marked as completed.
   - If not approved, the content is regenerated with the feedback.

7. **Final Result**: The final content is available through the job status endpoint.

## Using Webhooks

Webhooks allow your application to receive real-time notifications about job status changes. To use webhooks:

1. Provide a `webhook_url` parameter when starting a job.
2. Set up an endpoint in your application to receive POST requests.
3. Process the webhook data according to the job status.

Webhook payloads include:
- `job_id`: The ID of the job
- `status`: The current status (e.g., `pending_approval`, `completed`, `error`)
- `function`: The function that was called
- `result`: The result data (for completed jobs)

## Docker Deployment

Build and run the Docker container:

```bash
docker build -t crewai-hitl .
docker run -p 8888:8888 -v $(pwd)/.streamlit:/app/.streamlit crewai-hitl
``` 