# CrewAI Content Orchestrator with HITL

This project demonstrates how to use CrewAI with Human-in-the-Loop (HITL) capabilities for content generation. The system allows for asynchronous content creation with human feedback integration.

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
     --proxy-headers --forwarded-allow-ips "*" \
     --timeout-keep-alive 300 \
     --timeout-graceful-shutdown 300 --loop asyncio \
     --workers 1 --limit-concurrency 1000 \
     --backlog 2048 --no-server-header --no-date-header
   ```

2. Start the webhook receiver for testing (in a separate terminal):

   ```bash
   source .venv/bin/activate
   python webhook_receiver.py --port 8889
   ```

## Testing the HITL Workflow

You can test the HITL workflow using the provided test client:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Start a job and provide feedback (default behavior)
python hitl_test_client.py --topic "Climate Change Solutions" --webhook-url "http://localhost:8889/webhook"

# Start a job and approve the content without feedback
python hitl_test_client.py --topic "Space Exploration" --approve --webhook-url "http://localhost:8889/webhook"

# Start a job with custom feedback
python hitl_test_client.py --topic "Quantum Computing" --feedback "Please focus more on practical applications and less on theory." --webhook-url "http://localhost:8889/webhook"
```

### What to Expect During Testing

When you run the test client, you'll see:

1. The job being created and queued
2. Status updates as the job is processed
3. The initial content when it's ready for review
4. Feedback being submitted (or approval)
5. If feedback was provided, status updates as the content is revised
6. The final revised content

The webhook receiver will display notifications at key points in the process:

- When content is ready for human review
- When the job is completed after feedback

You can view all received webhooks by visiting <http://localhost:8889/> in your browser.

## API Endpoints

### Starting a Content Creation Job

```bash
curl -X POST "http://localhost:8888/kickoff" \
  -H "Content-Type: application/json" \
  -d '{
    "crew": "ContentCreationCrew",
    "inputs": {
      "topic": "Your Topic Here"
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

### Listing All Jobs

```bash
curl "http://localhost:8888/jobs"
```

### Listing Available Crews

```bash
curl "http://localhost:8888/list-crews"
```

## How the HITL Workflow Works

1. **Initial Request**: Client makes a request to `/kickoff` with the `ContentCreationCrew` crew.

2. **Background Processing**: The system processes the request asynchronously using CrewAI's crew framework.

3. **Pending Approval**: When content is ready for review, the job status changes to `pending_approval`.

4. **Webhook Notification**: If a webhook URL was provided, a notification is sent with the content for review.

5. **Human Review**: A human reviews the content and provides feedback.

6. **Feedback Processing**:
   - If approved, the job is marked as completed.
   - If not approved, the content is regenerated with the feedback using a specialized crew.

7. **Final Result**: The final content is available through the job status endpoint and a completion webhook is sent.

## Project Structure

- `orchestrator_service.py`: Contains the CrewAI implementation with agents, tasks, and crews
- `api_wrapper.py`: FastAPI wrapper that provides the API endpoints and job management
- `hitl_test_client.py`: Test client for the HITL workflow
- `webhook_receiver.py`: Simple webhook receiver for testing

The project follows CrewAI's recommended structure using the `@CrewBase` decorator along with `@agent`, `@task`, and `@crew` annotations to define the content creation workflow.

## Using Webhooks

Webhooks allow your application to receive real-time notifications about job status changes. To use webhooks:

1. Provide a `webhook_url` parameter when starting a job.
2. Set up an endpoint in your application to receive POST requests.
3. Process the webhook data according to the job status.

Webhook payloads include:

- `job_id`: The ID of the job
- `status`: The current status (e.g., `pending_approval`, `completed`, `error`)
- `crew`: The crew that was called
- `result`: The result data (for completed jobs)

## Docker Deployment

Build and run the Docker container:

```bash
docker build -t crewai-hitl .
docker run -p 8888:8888 -v $(pwd)/.streamlit:/app/.streamlit crewai-hitl
```
