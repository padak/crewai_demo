# CrewAI Content Orchestrator API Wrapper

> [!NOTE]
> This documentation explains how to use the CrewAI Content Orchestrator API Wrapper to expose your CrewAI agents and workflows as a RESTful API.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Integration Guide](#integration-guide)
  - [Code Structure Requirements](#code-structure-requirements)
  - [Environment Configuration](#environment-configuration)
- [API Endpoints](#api-endpoints)
  - [Health Check](#health-check)
  - [Kickoff Endpoint](#kickoff-endpoint)
  - [Job Status](#job-status)
  - [Feedback Endpoint](#feedback-endpoint)
  - [List Jobs](#list-jobs)
  - [List Crews](#list-crews)
  - [Delete Job](#delete-job)
- [Webhook Notifications](#webhook-notifications)
  - [Webhook Events](#webhook-events)
- [Job States](#job-states)
- [Implementation Examples](#implementation-examples)
  - [Basic Content Generation](#basic-content-generation)
  - [Human-in-the-Loop Workflow](#human-in-the-loop-workflow)
- [HITL Workflow Example](#hitl-workflow-example)
- [Environment Variables](#environment-variables)
  - [Required Variables](#required-variables)
  - [LLM Provider Configuration](#llm-provider-configuration)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)
  - [API Server Configuration](#api-server-configuration)
  - [Webhook Configuration](#webhook-configuration)
  - [Job Storage](#job-storage)
- [Security Best Practices](#security-best-practices)
- [Further Resources](#further-resources)

## Overview

The CrewAI Content Orchestrator API Wrapper (`api_wrapper.py`) is a FastAPI service that exposes your CrewAI agents and workflows as a RESTful API. This enables:

- **Asynchronous execution** of CrewAI workflows
- **Human-in-the-Loop (HITL)** approval processes
- **Webhook notifications** for job status updates
- **Job tracking** across multiple concurrent executions

## Quick Start

<details>
<summary>Click to expand quick start instructions</summary>

1. **Set up your environment**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Copy and configure environment variables
   cp .env.sample .env
   # Edit .env with your API keys
   ```

2. **Run the API service**:
   ```bash
   bash scripts/run_api.sh
   # Or directly with uvicorn:
   # uvicorn api_wrapper.api_wrapper:app --host 0.0.0.0 --port 8888 --timeout-keep-alive 300
   ```

3. **Make a request**:
   ```bash
   curl -X POST http://localhost:8888/kickoff \
     -H "Content-Type: application/json" \
     -d '{
       "crew": "ContentCreationCrew",
       "inputs": {
         "topic": "Artificial Intelligence"
       }
     }'
   ```
</details>

## Integration Guide

### Code Structure Requirements

The API wrapper supports two integration patterns:

#### 1. CrewBase Pattern (Recommended)

<details>
<summary>Click to see CrewBase pattern example</summary>

```python
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class MyContentCrew:
    """Content creation crew for generating articles"""
    
    def __init__(self, inputs=None):
        """Initialize with inputs from API"""
        self.inputs = inputs or {}
    
    @agent
    def researcher(self) -> Agent:
        """Define a research agent"""
        return Agent(
            role="Research Specialist",
            goal="Find comprehensive information on the topic",
            backstory="You are an expert researcher with years of experience",
            llm=self._get_llm(),
            verbose=True,
        )
    
    @task
    def research_task(self) -> Task:
        """Define a research task"""
        topic = self.inputs.get("topic", "General Knowledge")
        return Task(
            description=f"Research the topic: {topic}",
            expected_output="A detailed research report",
            agent=self.researcher(),
            human_input=False,
        )
    
    @crew
    def content_crew(self) -> Crew:
        """Define your crew - this will be discovered by the API wrapper"""
        return Crew(
            agents=[self.researcher()],
            tasks=[self.research_task()],
            process=Process.sequential,
            verbose=True,
        )
        
    def _get_llm(self):
        """Configure LLM based on environment variables"""
        # LLM configuration code here
```
</details>

The API wrapper automatically discovers methods decorated with `@crew` and makes them available as endpoints.

#### 2. Direct Function Pattern

> [!NOTE]
> The Direct Function Pattern is currently experimental and may not be fully supported in all versions of the API wrapper. The CrewBase Pattern is the recommended approach.

<details>
<summary>Click to see Direct Function pattern example (experimental)</summary>

```python
def create_content_with_hitl(
    topic: str, 
    feedback: str = None, 
    require_approval: bool = True
) -> Dict[str, Any]:
    """
    Content creation function with human-in-the-loop capability
    
    Args:
        topic: The topic to create content about
        feedback: Optional human feedback for refinement
        require_approval: Whether to require human approval
        
    Returns:
        Dictionary with content and status information
    """
    # Implementation here
    return {
        "status": "needs_approval",  # or "success" or "error"
        "content": "Generated content...",
        "length": 1234,
        "timestamp": datetime.now().isoformat(),
    }
```
</details>

### Environment Configuration

Set the path to your CrewAI code in the `DATA_APP_ENTRYPOINT` environment variable:

```bash
# In .env file
DATA_APP_ENTRYPOINT="crewai_app/orchestrator.py"
```

## API Endpoints

### Health Check

**Endpoint**: `GET /health`

Returns the health status of the API.

```bash
curl http://localhost:8888/health
```

<details>
<summary>Click to see response example</summary>

```json
{
  "status": "healthy",
  "timestamp": "2023-06-15T12:34:56.789012",
  "module_loaded": true,
  "active_jobs": 2
}
```
</details>

### Kickoff Endpoint

**Endpoint**: `POST /kickoff`

Starts a new content generation job.

<details>
<summary>Click to see request example</summary>

```bash
curl -X POST http://localhost:8888/kickoff \
  -H "Content-Type: application/json" \
  -d '{
    "crew": "ContentCreationCrew",
    "inputs": {
      "topic": "Artificial Intelligence",
      "require_approval": true
    },
    "webhook_url": "https://your-webhook-endpoint.com/webhook",
    "wait": false
  }'
```
</details>

**Parameters**:
- `crew` (string): The name of the crew class to use
- `inputs` (object): Input parameters for the crew
- `webhook_url` (string, optional): URL to receive job status updates
- `wait` (boolean, optional): Whether to wait for job completion (default: false)

> [!WARNING]
> The `wait=true` parameter is not currently functional. All jobs are processed asynchronously regardless of this setting.

<details>
<summary>Click to see response examples</summary>

**Response (Asynchronous)**:
```json
{
  "job_id": "987ca65a-62cf-4c48-850b-ad0eb3e37393",
  "status": "queued",
  "message": "Crew kickoff started in the background"
}
```

**Response (Synchronous, with wait=true)**:
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
</details>

### Job Status

**Endpoint**: `GET /job/{job_id}`

Retrieves the status and result of a specific job.

```bash
curl http://localhost:8888/job/987ca65a-62cf-4c48-850b-ad0eb3e37393
```

<details>
<summary>Click to see response example</summary>

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
</details>

### Feedback Endpoint

**Endpoint**: `POST /job/{job_id}/feedback`

Provides human feedback for a job that's pending approval.

<details>
<summary>Click to see request example</summary>

```bash
curl -X POST http://localhost:8888/job/987ca65a-62cf-4c48-850b-ad0eb3e37393/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "Please make the content more concise and add more examples.",
    "approved": false
  }'
```
</details>

**Parameters**:
- `feedback` (string): Human feedback on the content
- `approved` (boolean): Whether to approve the content as is

<details>
<summary>Click to see response examples</summary>

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
</details>

### List Jobs

**Endpoint**: `GET /jobs`

Lists all jobs with optional filtering.

```bash
curl "http://localhost:8888/jobs?limit=5&status=completed"
```

**Query Parameters**:
- `limit` (integer, optional): Maximum number of jobs to return (default: 10)
- `status` (string, optional): Filter jobs by status

<details>
<summary>Click to see response example</summary>

```json
{
  "jobs": [
    {
      "id": "987ca65a-62cf-4c48-850b-ad0eb3e37393",
      "crew": "ContentCreationCrew",
      "status": "completed",
      "created_at": "2023-06-15T12:34:56.789012",
      "completed_at": "2023-06-15T12:40:56.789012"
    }
  ],
  "count": 1,
  "total_jobs": 15
}
```
</details>

### List Crews

**Endpoint**: `GET /list-crews`

Lists all available crews that can be used with the kickoff endpoint.

```bash
curl http://localhost:8888/list-crews
```

<details>
<summary>Click to see response example</summary>

```json
{
  "crews": [
    "ContentCreationCrew",
    "content_crew",
    "content_crew_with_feedback"
  ]
}
```
</details>

### Delete Job

**Endpoint**: `DELETE /job/{job_id}`

Deletes a job and its associated data.

```bash
curl -X DELETE http://localhost:8888/job/987ca65a-62cf-4c48-850b-ad0eb3e37393
```

<details>
<summary>Click to see response example</summary>

```json
{
  "message": "Job deleted successfully",
  "job_id": "987ca65a-62cf-4c48-850b-ad0eb3e37393"
}
```
</details>

## Webhook Notifications

The API wrapper can send webhook notifications to a URL you provide when a job's status changes.

<details>
<summary>Click to see webhook payload example</summary>

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
</details>

### Webhook Events

The following events trigger webhook notifications:

1. **Job Completed**: When a job finishes successfully
2. **Job Error**: When a job encounters an error
3. **Pending Approval**: When a job is waiting for human approval

## Job States

A job can be in one of the following states:

- **queued**: Job has been created and is waiting to be processed
- **processing**: Job is currently being processed
- **pending_approval**: Job is waiting for human approval
- **completed**: Job has completed successfully
- **error**: Job encountered an error

## Implementation Examples

### Basic Content Generation

<details>
<summary>Click to see basic content generation example</summary>

```python
# In orchestrator.py
@CrewBase
class ContentCreationCrew:
    """Content creation crew for generating articles"""
    
    def __init__(self, inputs=None):
        self.inputs = inputs or {}
    
    @agent
    def writer_agent(self) -> Agent:
        return Agent(
            role="Content Writer",
            goal="Create engaging content",
            backstory="You are a skilled writer",
            llm=self._get_llm(),
            verbose=True,
        )
    
    @task
    def writing_task(self) -> Task:
        topic = self.inputs.get("topic", "General Knowledge")
        return Task(
            description=f"Write about {topic}",
            expected_output="A well-structured article",
            agent=self.writer_agent(),
            human_input=False,
        )
    
    @crew
    def content_crew(self) -> Crew:
        return Crew(
            agents=[self.writer_agent()],
            tasks=[self.writing_task()],
            process=Process.sequential,
            verbose=True,
        )
    
    def _get_llm(self):
        # Use OPENAI_API_KEY for OpenRouter
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set")
        
        return ChatOpenAI(
            model="openai/gpt-4o-mini",
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.7,
        )
```
</details>

### Human-in-the-Loop Workflow

<details>
<summary>Click to see HITL workflow implementation example</summary>

```python
# In orchestrator.py
@CrewBase
class ContentCreationCrew:
    # ... other methods ...
    
    @task
    def editing_with_feedback_task(self) -> Task:
        feedback = self.inputs.get("feedback", "Please improve the content.")
        return Task(
            description=f"Edit the content incorporating this feedback: {feedback}",
            expected_output="A polished article addressing the feedback",
            agent=self.editor_agent(),
            context=[self.writing_task()],
            human_input=False,
        )
    
    @crew
    def content_crew_with_feedback(self) -> Crew:
        return Crew(
            agents=[self.writer_agent(), self.editor_agent()],
            tasks=[self.writing_task(), self.editing_with_feedback_task()],
            process=Process.sequential,
            verbose=True,
        )
```
</details>

## HITL Workflow Example

> [!TIP]
> Human-in-the-Loop (HITL) workflows allow for human feedback and approval during the content generation process.

<details>
<summary>Click to see complete HITL workflow example</summary>

1. **Start a job requiring approval**:
   ```bash
   curl -X POST http://localhost:8888/kickoff \
     -H "Content-Type: application/json" \
     -d '{
       "crew": "ContentCreationCrew",
       "inputs": {
         "topic": "Climate Change",
         "require_approval": true
       }
     }'
   ```

2. **Check job status until it's pending approval**:
   ```bash
   curl http://localhost:8888/job/YOUR_JOB_ID
   ```

3. **Provide feedback or approve**:
   ```bash
   # To approve:
   curl -X POST http://localhost:8888/job/YOUR_JOB_ID/feedback \
     -H "Content-Type: application/json" \
     -d '{
       "feedback": "Content approved as is.",
       "approved": true
     }'
   
   # To request changes:
   curl -X POST http://localhost:8888/job/YOUR_JOB_ID/feedback \
     -H "Content-Type: application/json" \
     -d '{
       "feedback": "Please add more examples about renewable energy.",
       "approved": false
     }'
   ```

4. **If feedback was provided, check status again** until it's "pending_approval" again, then review the updated content.
</details>

## Environment Variables

> [!IMPORTANT]
> Make sure to set all required environment variables before running the API wrapper.

### Required Variables

- `DATA_APP_ENTRYPOINT`: Path to your CrewAI code file (e.g., `crewai_app/orchestrator.py`)

### LLM Provider Configuration

<details>
<summary>OpenRouter Configuration (Default)</summary>

- `LLM_PROVIDER=openrouter`: Set to use OpenRouter
- `OPENAI_API_KEY`: Your API key for OpenRouter
- `OPENAI_API_BASE=https://openrouter.ai/api/v1`: The OpenRouter API base URL
- `OPENROUTER_MODEL=openai/gpt-4o-mini`: The model to use
</details>

<details>
<summary>Azure OpenAI Configuration</summary>

- `LLM_PROVIDER=azure`: Set to use Azure OpenAI
- `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint URL
- `AZURE_OPENAI_API_VERSION=2023-05-15`: The API version
- `AZURE_OPENAI_DEPLOYMENT_ID=gpt-35-turbo-0125`: The deployment ID
</details>

## Troubleshooting

> [!WARNING]
> Common issues you might encounter when using the API wrapper and how to solve them.

<details>
<summary>Module Loading Issues</summary>

**Problem**: API fails to load your module
```
Error: Failed to load user script: No module named 'crewai_app'
```

**Solutions**:
- Verify `DATA_APP_ENTRYPOINT` is set correctly in your `.env` file
- Ensure the Python path includes your project root
- Check that the file exists and has the correct permissions
</details>

<details>
<summary>Crew Discovery Issues</summary>

**Problem**: API can't find your crew
```
Error: Crew ContentCreationCrew not found in user module
```

**Solutions**:
- Ensure your class is decorated with `@CrewBase`
- Check that at least one method is decorated with `@crew`
- Verify the class name matches what you're passing to the API
</details>

<details>
<summary>API Key Issues</summary>

**Problem**: Authentication errors with LLM providers
```
Error: OPENAI_API_KEY must be set for OpenRouter
```

**Solutions**:
- Set `OPENAI_API_KEY` in your `.env` file
- For Azure, ensure `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` are set
- Verify the API keys are valid and have not expired
</details>

<details>
<summary>Job Execution Issues</summary>

**Problem**: Jobs fail to execute or get stuck
```
Error: 'NoneType' object has no attribute 'kickoff'
```

**Solutions**:
- Check that your crew method returns a valid Crew object
- Ensure all required inputs are provided
- Look for exceptions in your agent or task code
- Verify LLM configuration is correct
</details>

## Advanced Configuration

### API Server Configuration

```bash
# In .env file
API_HOST=0.0.0.0
API_PORT=8888
API_WORKERS=1
API_LOG_LEVEL=info
```

### Webhook Configuration

```bash
# In .env file
WEBHOOK_RETRY_ATTEMPTS=3
WEBHOOK_RETRY_DELAY=5
```

### Job Storage

```bash
# In .env file
JOB_STORAGE_TYPE=memory  # or 'redis'
REDIS_URL=redis://localhost:6379/0  # if using redis
```

## Security Best Practices

> [!CAUTION]
> Implementing proper security measures is crucial when deploying to production environments.

When deploying to production:

1. **Use HTTPS** with a valid SSL certificate
2. **Implement authentication** using API keys or OAuth
3. **Restrict CORS** to trusted domains only
4. **Validate webhook URLs** against a whitelist
5. **Set appropriate timeouts** for long-running operations
6. **Monitor and rate limit** requests to prevent abuse

## Further Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [Azure OpenAI Integration](azure_openai_integration.md)
- [HITL Workflow](HITL_WORKFLOW.md)
- [HITL Implementation](HITL_IMPLEMENTATION.md) 