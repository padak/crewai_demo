# CrewAI Content Orchestrator API Wrapper Documentation

## Overview

The CrewAI Content Orchestrator API Wrapper (`api_wrapper.py`) is a FastAPI-based service that allows you to expose your CrewAI agents and workflows as a RESTful API. This enables you to:

1. Run CrewAI workflows asynchronously
2. Implement Human-in-the-Loop (HITL) approval processes
3. Receive webhook notifications for job status updates
4. Track and manage multiple concurrent jobs

This documentation explains how to integrate your CrewAI code with the API wrapper and how to interact with the exposed endpoints.

## Table of Contents

- [Integration Guide](#integration-guide)
  - [Required Code Structure](#required-code-structure)
  - [CrewBase Integration](#crewbase-integration)
  - [Direct Function Integration](#direct-function-integration)
- [API Endpoints](#api-endpoints)
  - [Health Check](#health-check)
  - [Kickoff Endpoint](#kickoff-endpoint)
  - [Job Status](#job-status)
  - [Feedback Endpoint](#feedback-endpoint)
  - [List Jobs](#list-jobs)
  - [Delete Job](#delete-job)
  - [List Crews](#list-crews)
- [Webhook Notifications](#webhook-notifications)
  - [Webhook Payload Structure](#webhook-payload-structure)
  - [Webhook Events](#webhook-events)
- [Job States](#job-states)
- [Example Workflows](#example-workflows)
  - [Direct Mode Workflow](#direct-mode-workflow)
  - [HITL Workflow](#hitl-workflow)
- [Error Handling](#error-handling)
- [Security Considerations](#security-considerations)
- [Environment Variables](#environment-variables)

## Integration Guide

### Required Code Structure

The API wrapper expects your code to follow one of two patterns:

1. **CrewBase Classes**: Using the `@CrewBase` decorator from CrewAI's project module
2. **Direct Functions**: Implementing a specific function called `create_content_with_hitl`

Your code should be in a Python file specified by the `DATA_APP_ENTRYPOINT` environment variable.

### CrewBase Integration

If you're using CrewAI's `@CrewBase` decorator, your code should look like this:

```python
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class MyContentCrew:
    """Your crew description"""
    
    @agent
    def my_agent(self) -> Agent:
        """Define your agent"""
        return Agent(...)
    
    @task
    def my_task(self, inputs=None) -> Task:
        """Define your task"""
        return Task(...)
    
    @crew
    def my_crew(self) -> Crew:
        """Define your crew - this method will be discovered by the API wrapper"""
        return Crew(
            agents=[self.my_agent()],
            tasks=[self.my_task()],
            process=Process.sequential
        )
```

The API wrapper will automatically discover methods decorated with `@crew` and use them to create and run crews.

### Direct Function Integration

Alternatively, you can implement a function called `create_content_with_hitl` with this signature:

```python
def create_content_with_hitl(topic: str, feedback: str = None, require_approval: bool = True) -> Dict[str, Any]:
    """
    Content creation function with human-in-the-loop capability
    Args:
        topic: The topic to create content about
        feedback: Optional human feedback for refinement
        require_approval: Whether to require human approval (default: True)
    Returns:
        Dictionary with content, execution details, and human approval status
    """
    # Your implementation here
    # Should return a dictionary with at least these keys:
    # - status: "success", "needs_approval", or "error"
    # - content: The generated content
    # - length: Length of the content
    # - timestamp: When the content was generated
    # - feedback_incorporated: Whether feedback was used (if applicable)
```

## API Endpoints

### Health Check

**Endpoint**: `GET /health`

Returns the health status of the API.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2023-06-15T12:34:56.789012",
  "module_loaded": true,
  "active_jobs": 2
}
```

### Kickoff Endpoint

**Endpoint**: `POST /kickoff`

Starts a new content generation job.

**Request Body**:
```json
{
  "crew": "ContentCreationCrew",
  "inputs": {
    "topic": "Artificial Intelligence",
    "require_approval": false
  },
  "webhook_url": "https://your-webhook-endpoint.com/webhook",
  "wait": false
}
```

**Parameters**:
- `crew` (string): The name of the crew class to use
- `inputs` (object): Input parameters for the crew
  - `topic` (string): The topic for content generation
  - `require_approval` (boolean): Whether human approval is required
  - Other parameters specific to your crew
- `webhook_url` (string, optional): URL to receive job status updates
- `wait` (boolean, optional): Whether to wait for job completion (synchronous execution)

**Response (Asynchronous)**:
```json
{
  "job_id": "987ca65a-62cf-4c48-850b-ad0eb3e37393",
  "status": "queued",
  "message": "Crew kickoff started in the background"
}
```

**Response (Synchronous)**:
```json
{
  "job_id": "987ca65a-62cf-4c48-850b-ad0eb3e37393",
  "status": "completed",
  "result": {
    "content": "Generated content...",
    "length": 1234
  }
}
```

### Job Status

**Endpoint**: `GET /job/{job_id}`

Retrieves the status and result of a specific job.

**Response**:
```json
{
  "id": "987ca65a-62cf-4c48-850b-ad0eb3e37393",
  "crew": "ContentCreationCrew",
  "inputs": {
    "topic": "Artificial Intelligence"
  },
  "status": "completed",
  "created_at": "2023-06-15T12:34:56.789012",
  "completed_at": "2023-06-15T12:40:56.789012",
  "result": {
    "content": "Generated content...",
    "length": 1234
  }
}
```

### Feedback Endpoint

**Endpoint**: `POST /job/{job_id}/feedback`

Provides human feedback for a job that's pending approval.

**Request Body**:
```json
{
  "feedback": "Please make the content more concise and add more examples.",
  "approved": false
}
```

**Parameters**:
- `feedback` (string): Human feedback on the content
- `approved` (boolean): Whether to approve the content as is

**Response (Approved)**:
```json
{
  "message": "Feedback recorded and job marked as completed",
  "job_id": "987ca65a-62cf-4c48-850b-ad0eb3e37393"
}
```

**Response (Not Approved)**:
```json
{
  "message": "Feedback recorded and content generation restarted with feedback",
  "job_id": "987ca65a-62cf-4c48-850b-ad0eb3e37393"
}
```

### List Jobs

**Endpoint**: `GET /jobs`

Lists all jobs with optional filtering.

**Query Parameters**:
- `limit` (integer, optional): Maximum number of jobs to return (default: 10)
- `status` (string, optional): Filter jobs by status

**Response**:
```json
{
  "jobs": [
    {
      "id": "987ca65a-62cf-4c48-850b-ad0eb3e37393",
      "crew": "ContentCreationCrew",
      "status": "completed",
      "created_at": "2023-06-15T12:34:56.789012",
      "completed_at": "2023-06-15T12:40:56.789012",
      "has_result": true,
      "has_error": false
    }
  ],
  "count": 1,
  "total_jobs": 5
}
```

### Delete Job

**Endpoint**: `DELETE /job/{job_id}`

Deletes a specific job.

**Response**:
```json
{
  "message": "Job 987ca65a-62cf-4c48-850b-ad0eb3e37393 deleted successfully"
}
```

### List Crews

**Endpoint**: `GET /list-crews`

Lists all available crews in the system.

**Response**:
```json
{
  "crews": ["ContentCreationCrew", "ResearchCrew"]
}
```

## Webhook Notifications

The API wrapper can send webhook notifications to a URL you provide when a job's status changes.

### Webhook Payload Structure

```json
{
  "job_id": "987ca65a-62cf-4c48-850b-ad0eb3e37393",
  "status": "completed",
  "crew": "ContentCreationCrew",
  "completed_at": "2023-06-15T12:40:56.789012",
  "result": {
    "content": "Generated content...",
    "length": 1234
  }
}
```

### Webhook Events

The following events trigger webhook notifications:

1. **Job Completed**: When a job finishes successfully
   ```json
   {
     "job_id": "987ca65a-62cf-4c48-850b-ad0eb3e37393",
     "status": "completed",
     "crew": "ContentCreationCrew",
     "completed_at": "2023-06-15T12:40:56.789012",
     "result": {
       "content": "Generated content...",
       "length": 1234
     }
   }
   ```

2. **Job Error**: When a job encounters an error
   ```json
   {
     "job_id": "987ca65a-62cf-4c48-850b-ad0eb3e37393",
     "status": "error",
     "crew": "ContentCreationCrew",
     "error_at": "2023-06-15T12:38:56.789012",
     "error": "Error message",
     "error_type": "ValueError"
   }
   ```

3. **Pending Approval**: When a job is waiting for human approval
   ```json
   {
     "job_id": "987ca65a-62cf-4c48-850b-ad0eb3e37393",
     "status": "pending_approval",
     "crew": "ContentCreationCrew",
     "result": {
       "content": "Generated content...",
       "length": 1234
     }
   }
   ```

> **Note**: For testing webhook functionality locally, a simple webhook receiver (`webhook_receiver.py`) is included in the project. This is intended for development purposes only and should not be used in production.

## Job States

A job can be in one of the following states:

1. **queued**: Job has been created and is waiting to be processed
2. **processing**: Job is currently being processed
3. **pending_approval**: Job is waiting for human approval
4. **completed**: Job has completed successfully
5. **error**: Job encountered an error

## Example Workflows

### Direct Mode Workflow

1. Start a job without requiring approval:
   ```bash
   curl -X POST https://your-api-url/kickoff \
     -H "Content-Type: application/json" \
     -d '{
       "crew": "ContentCreationCrew",
       "inputs": {
         "topic": "Artificial Intelligence",
         "require_approval": false
       }
     }'
   ```

2. Get the job ID from the response and check status:
   ```bash
   curl https://your-api-url/job/YOUR_JOB_ID
   ```

3. Once status is "completed", retrieve the content from the result.

### HITL Workflow

1. Start a job requiring approval:
   ```bash
   curl -X POST https://your-api-url/kickoff \
     -H "Content-Type: application/json" \
     -d '{
       "crew": "ContentCreationCrew",
       "inputs": {
         "topic": "Climate Change",
         "require_approval": true
       }
     }'
   ```

2. Get the job ID from the response and check status:
   ```bash
   curl https://your-api-url/job/YOUR_JOB_ID
   ```

3. Once status is "pending_approval", review the content and either:

   a. Approve the content:
   ```bash
   curl -X POST https://your-api-url/job/YOUR_JOB_ID/feedback \
     -H "Content-Type: application/json" \
     -d '{
       "feedback": "Content approved as is.",
       "approved": true
     }'
   ```

   b. Provide feedback for improvement:
   ```bash
   curl -X POST https://your-api-url/job/YOUR_JOB_ID/feedback \
     -H "Content-Type: application/json" \
     -d '{
       "feedback": "Please add more examples about renewable energy.",
       "approved": false
     }'
   ```

4. If feedback was provided, check status again until it's "pending_approval" again, then review the updated content.

5. Once approved, the status will change to "completed".

## Error Handling

The API wrapper provides detailed error information when something goes wrong:

```json
{
  "id": "987ca65a-62cf-4c48-850b-ad0eb3e37393",
  "crew": "ContentCreationCrew",
  "inputs": {
    "topic": "Artificial Intelligence"
  },
  "status": "error",
  "created_at": "2023-06-15T12:34:56.789012",
  "error_at": "2023-06-15T12:38:56.789012",
  "error": "Error message",
  "error_type": "ValueError"
}
```

Common error scenarios:
- Crew not found
- Invalid inputs
- Execution errors in your code
- Timeout errors

## Security Considerations

The API wrapper includes several security features:

1. **CORS Middleware**: Controls which domains can access the API
2. **Trusted Host Middleware**: Restricts which hosts can make requests
3. **Environment Variables**: Sensitive information is loaded from environment variables or a secrets file

When deploying to production, consider:
- Using HTTPS
- Implementing authentication
- Restricting webhook URLs to trusted domains
- Setting appropriate timeouts for long-running operations

## Environment Variables

The API wrapper uses the following environment variables:

- `DATA_APP_ENTRYPOINT`: Path to your Python script containing CrewAI code (required)
- `OPENROUTER_API_KEY`: API key for OpenRouter (if using OpenRouter for LLM access)
- Other environment variables specific to your CrewAI implementation

You can set these variables in a `.streamlit/secrets.toml` file, which will be loaded automatically by the API wrapper. 