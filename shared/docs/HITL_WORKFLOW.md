# Human-in-the-Loop (HITL) Workflow with CrewAI

This document explains how to use the Human-in-the-Loop (HITL) workflow with the CrewAI Content Orchestrator, focusing on the webhook-based approach for maximum efficiency.

## Overview

The HITL workflow allows you to:

1. Start a content generation job
2. Receive a notification when the content is ready for review
3. Review the content and either:
   - Approve it as is
   - Provide feedback for improvements
4. Receive the final content after approval or revision

## Setup

### 1. Start the API Wrapper Service

First, make sure the API wrapper service is running:

```bash
# Use the provided script
./scripts/run_api.sh

# Or manually:
source .venv/bin/activate
export DATA_APP_ENTRYPOINT="crewai_app/orchestrator.py"
uvicorn api_wrapper.api_wrapper:app --host 0.0.0.0 --port 8888 --timeout-keep-alive 300 --timeout-graceful-shutdown 300 --loop asyncio
```

### 2. Start the Webhook Receiver

In a separate terminal, start the webhook receiver:

```bash
source .venv/bin/activate
python scripts/webhook_receiver.py --host 0.0.0.0 --port 8889
```

This will start a simple webhook receiver that listens for notifications from the API wrapper service. The webhook URL will be `http://localhost:8889/webhook`.

## Using the HITL Workflow

### Starting a New Job

To start a new content generation job with HITL:

```bash
# Use the provided script
./scripts/hitl_mode_example.sh

# Or manually with the API client:
python api_wrapper/api_client.py --topic "Quantum Computing" --mode hitl --webhook http://localhost:8889/webhook
```

This command:
- Starts a new content generation job on the topic "Quantum Computing"
- Uses the HITL workflow (requires human approval)
- Sends webhook notifications to the webhook receiver

The output will include a job ID that you can use to check the status or provide feedback later.

### Monitoring Job Status

You can monitor the job status in several ways:

1. **Webhook Receiver**: The webhook receiver will display notifications when:
   - The job is created
   - The job requires approval
   - The job is completed
   - Any errors occur

2. **API Endpoint**: You can check the job status directly:
   ```bash
   curl http://localhost:8888/job/{job_id}
   ```

### Providing Feedback or Approval

When the job reaches the "pending_approval" state, you can either approve the content or provide feedback:

#### Approving Content

```bash
python api_wrapper/api_client.py --job-id "your-job-id" --approve
```

This will approve the content as is, and the job will be marked as completed.

#### Providing Feedback

```bash
python api_wrapper/api_client.py --job-id "your-job-id" --feedback "Please add more examples of practical applications of quantum computing"
```

This will send your feedback to the API wrapper service, which will then revise the content based on your feedback.

## Workflow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │
│  api_client │────▶│ api_wrapper │────▶│ CrewAI      │
│             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │                   │                   │
       │                   ▼                   │
       │           ┌─────────────┐            │
       │           │             │            │
       └──────────▶│  webhook    │◀───────────┘
                   │  receiver   │
                   │             │
                   └─────────────┘
```

## Best Practices

1. **Always Use Webhooks**: For HITL workflows, it's best to use webhooks instead of polling. This allows you to:
   - Start multiple jobs concurrently
   - Receive notifications when jobs require attention
   - Avoid unnecessary polling requests

2. **Provide Specific Feedback**: When providing feedback, be as specific as possible to get the best results.

3. **Use Async Mode for Efficiency**: For better performance, use the `--async` flag:
   ```bash
   python api_wrapper/api_client.py --topic "Quantum Computing" --mode hitl --webhook http://localhost:8889/webhook --async
   ```

## Troubleshooting

### Job Stuck in Processing

If a job seems stuck in the "processing" state for too long:

1. Check the API wrapper logs for errors
2. Verify that the CrewAI service is running correctly
3. Restart the API wrapper service if necessary

### Webhook Notifications Not Received

If you're not receiving webhook notifications:

1. Make sure the webhook receiver is running
2. Check that the webhook URL is correct
3. Verify that there are no network issues between the API wrapper and webhook receiver

### Invalid Job ID

If you get an error about an invalid job ID:

1. Make sure you're using the correct job ID
2. Check if the job has expired (jobs are stored in memory and may be lost if the service restarts)

## Example Workflow

Here's a complete example workflow:

1. Start the webhook receiver:
   ```bash
   python scripts/webhook_receiver.py
   ```

2. Start a new job:
   ```bash
   python api_wrapper/api_client.py --topic "Artificial Intelligence Ethics" --mode hitl --webhook http://localhost:8889/webhook
   ```

3. Wait for the webhook notification that the job requires approval

4. Provide feedback:
   ```bash
   python api_wrapper/api_client.py --job-id "your-job-id" --feedback "Please focus more on the ethical implications for privacy"
   ```

5. Wait for the webhook notification that the job is completed

6. View the final content:
   ```bash
   curl http://localhost:8888/job/your-job-id
   ``` 