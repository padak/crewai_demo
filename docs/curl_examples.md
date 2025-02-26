# CrewAI Content Orchestrator API - curl Examples

This document provides examples of how to interact with the CrewAI Content Orchestrator API using curl commands.

## Table of Contents
- [Health Check](#health-check)
- [Direct Content Generation](#direct-content-generation)
- [HITL Content Generation](#hitl-content-generation)
- [Check Job Status](#check-job-status)
- [Provide Feedback](#provide-feedback)
- [Approve Content](#approve-content)
- [List Jobs](#list-jobs)
- [List Available Crews](#list-available-crews)

## Health Check

Check if the API is running:

```bash
curl https://flask-550.hub.canary-orion.keboola.dev/health
```

## Direct Content Generation

Generate content directly without human approval:

```bash
# Asynchronous (non-blocking)
curl -X POST https://flask-550.hub.canary-orion.keboola.dev/kickoff \
  -H "Content-Type: application/json" \
  -d '{
    "crew": "ContentCreationCrew",
    "inputs": {
      "topic": "Artificial Intelligence",
      "require_approval": false
    }
  }'

# Synchronous (wait for result)
curl -X POST https://flask-550.hub.canary-orion.keboola.dev/kickoff \
  -H "Content-Type: application/json" \
  -d '{
    "crew": "ContentCreationCrew",
    "inputs": {
      "topic": "Artificial Intelligence",
      "require_approval": false
    },
    "wait": true
  }'
```

## HITL Content Generation

Generate content with Human-in-the-Loop workflow:

```bash
# Without webhook
curl -X POST https://flask-550.hub.canary-orion.keboola.dev/kickoff \
  -H "Content-Type: application/json" \
  -d '{
    "crew": "ContentCreationCrew",
    "inputs": {
      "topic": "Climate Change",
      "require_approval": true
    }
  }'

# With webhook for notifications
curl -X POST https://flask-550.hub.canary-orion.keboola.dev/kickoff \
  -H "Content-Type: application/json" \
  -d '{
    "crew": "ContentCreationCrew",
    "inputs": {
      "topic": "Climate Change",
      "require_approval": true
    },
    "webhook_url": "http://localhost:8889/webhook"
  }'
```

## Check Job Status

Check the status of a specific job:

```bash
curl https://flask-550.hub.canary-orion.keboola.dev/job/YOUR_JOB_ID
```

Replace `YOUR_JOB_ID` with the actual job ID returned from the kickoff request.

## Provide Feedback

Provide feedback for a job that's pending approval:

```bash
curl -X POST https://flask-550.hub.canary-orion.keboola.dev/job/YOUR_JOB_ID/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "Please make the content more concise and add more examples about renewable energy.",
    "approved": false
  }'
```

## Approve Content

Approve content for a job that's pending approval:

```bash
curl -X POST https://flask-550.hub.canary-orion.keboola.dev/job/YOUR_JOB_ID/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "Content approved as is.",
    "approved": true
  }'
```

## List Jobs

List all jobs (with optional filtering):

```bash
# List all jobs (limited to 10)
curl https://flask-550.hub.canary-orion.keboola.dev/jobs

# List jobs with a specific status
curl https://flask-550.hub.canary-orion.keboola.dev/jobs?status=completed

# List more jobs
curl https://flask-550.hub.canary-orion.keboola.dev/jobs?limit=20
```

## List Available Crews

List all available crews in the system:

```bash
curl https://flask-550.hub.canary-orion.keboola.dev/list-crews
```

## Delete a Job

Delete a specific job:

```bash
curl -X DELETE https://flask-550.hub.canary-orion.keboola.dev/job/YOUR_JOB_ID
```

## Example Workflow

Here's a complete example workflow using curl:

1. Start a HITL job:
```bash
curl -X POST https://flask-550.hub.canary-orion.keboola.dev/kickoff \
  -H "Content-Type: application/json" \
  -d '{
    "crew": "ContentCreationCrew",
    "inputs": {
      "topic": "Renewable Energy",
      "require_approval": true
    }
  }' | jq
```

2. Save the job ID from the response:
```bash
export JOB_ID="job_id_from_response"
```

3. Check job status until it's pending approval:
```bash
curl https://flask-550.hub.canary-orion.keboola.dev/job/$JOB_ID | jq
```

4. Provide feedback:
```bash
curl -X POST https://flask-550.hub.canary-orion.keboola.dev/job/$JOB_ID/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "Please add more examples about solar power.",
    "approved": false
  }' | jq
```

5. Check job status again until it's completed:
```bash
curl https://flask-550.hub.canary-orion.keboola.dev/job/$JOB_ID | jq
```

Note: The `jq` command is used to format the JSON response. If you don't have it installed, you can omit it. 