# CrewAI Demo

This repository contains a demo of using CrewAI for content generation with human-in-the-loop capabilities, along with an API wrapper to serve the CrewAI application.

## Project Structure

The project is organized into the following components:

```
crewai_demo/                  # Root project directory
│
├── crewai_app/               # CrewAI application
│   ├── orchestrator.py       # Main orchestrator for CrewAI
│   ├── agents/               # Agent definitions
│   ├── tasks/                # Task definitions
│   └── tests/                # Tests for CrewAI app
│
├── api_wrapper/              # API wrapper service
│   ├── api_wrapper.py        # Main API service
│   ├── api_client.py         # Client for the API
│   └── tests/                # Tests for API service
│
├── shared/                   # Shared resources
│   └── docs/                 # Documentation
│
├── scripts/                  # Utility scripts
│
├── .env.sample              # Environment variable templates
├── .env.azure.sample
└── requirements.txt         # Project dependencies
```

## Components

### CrewAI Application

The `crewai_app` directory contains the core CrewAI application, which is responsible for content generation using AI agents. The main components are:

- `orchestrator.py`: The main orchestrator that defines the CrewAI crew, agents, and tasks.
- `agents/`: Definitions of AI agents used in the content creation process.
- `tasks/`: Definitions of tasks that the agents perform.
- `tests/`: Tests for the CrewAI application, including integration tests for different LLM providers.

### API Wrapper

The `api_wrapper` directory contains the API service that wraps the CrewAI application and exposes it via a REST API. The main components are:

- `api_wrapper.py`: The main FastAPI application that provides endpoints for interacting with the CrewAI application.
- `api_client.py`: A client for the API that can be used to interact with the API programmatically.
- `tests/`: Tests for the API service.

### Shared Resources

The `shared` directory contains resources that are used by both the CrewAI application and the API wrapper, such as documentation.

### Scripts

The `scripts` directory contains utility scripts for working with the application, such as webhook receivers, curl examples, and job checking scripts.

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.sample` to `.env` and fill in your API keys
4. Run the API wrapper: `uvicorn api_wrapper.api_wrapper:app --reload`
5. Use the API client or curl to interact with the API

## Documentation

For more detailed documentation, see the files in the `shared/docs/` directory:

- [Azure OpenAI Integration](shared/docs/azure_openai_integration.md)
- [API Wrapper Documentation](shared/docs/api_wrapper_documentation.md)
- [HITL Workflow](shared/docs/HITL_WORKFLOW.md)
- [HITL Implementation](shared/docs/HITL_IMPLEMENTATION.md)

## Testing

To test the CrewAI application with different LLM providers:

```bash
# Test Azure OpenAI
python -m crewai_app.tests.test_azure_openai

# Test OpenRouter
python -m crewai_app.tests.test_openrouter

# Test CrewAI integration
python -m crewai_app.tests.test_crewai_integration
```

## License

[MIT License](LICENSE)
