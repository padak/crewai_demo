# Azure OpenAI Integration

This document explains how to use Azure OpenAI with the CrewAI Content Orchestrator.

## Overview

The CrewAI Content Orchestrator now supports both OpenRouter and Azure OpenAI as LLM providers. This gives you flexibility in choosing your preferred provider based on your needs.

## Configuration

To use Azure OpenAI, you need to set the following environment variables:

1. `LLM_PROVIDER=azure` - This tells the system to use Azure OpenAI instead of OpenRouter
2. `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key
3. `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI endpoint URL (e.g., "https://your-resource-name.openai.azure.com/")
4. `AZURE_OPENAI_API_VERSION` - (Optional) The API version to use (defaults to "2023-05-15")
5. `AZURE_OPENAI_DEPLOYMENT_ID` - (Optional) The deployment ID to use (defaults to "gpt-35-turbo-0125")

You can set these variables in your `.streamlit/secrets.toml` file:

```toml
LLM_PROVIDER = "azure"
AZURE_OPENAI_API_KEY = "your-api-key"
AZURE_OPENAI_ENDPOINT = "https://your-resource-name.openai.azure.com/"
AZURE_OPENAI_API_VERSION = "2023-05-15"  # Optional
AZURE_OPENAI_DEPLOYMENT_ID = "gpt-35-turbo-0125"  # Optional
```

Or in your `.env` file:

```bash
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2023-05-15  # Optional
AZURE_OPENAI_DEPLOYMENT_ID=gpt-35-turbo-0125  # Optional
```

## Implementation Details

The system uses the `AzureChatOpenAI` class from `langchain_openai` when `LLM_PROVIDER` is set to `azure`. This class is specifically designed to work with Azure OpenAI deployments and handles the authentication and API calls differently from the standard OpenAI integration.

Here's how the implementation works in the `_get_llm` method of the `orchestrator.py` file:

```python
if llm_provider == "azure":
    # Azure OpenAI configuration
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")
    deployment_id = os.environ.get("AZURE_OPENAI_DEPLOYMENT_ID", "gpt-35-turbo-0125")
    
    if not api_key or not azure_endpoint:
        raise ValueError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT must be set for Azure OpenAI")
    
    logger.info(f"Using Azure OpenAI with deployment_id: {deployment_id}")
    
    # Import the dedicated Azure class
    from langchain_openai import AzureChatOpenAI
    
    # For Azure OpenAI, we use the dedicated AzureChatOpenAI class
    return AzureChatOpenAI(
        azure_deployment=deployment_id,
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=azure_endpoint,
        temperature=0.7,
    )
```

## Deployment IDs

Azure OpenAI uses deployment IDs instead of model names. The default deployment ID is `gpt-35-turbo-0125`, but you can specify a different one by setting the `AZURE_OPENAI_DEPLOYMENT_ID` environment variable.

Supported deployment IDs include:
- `gpt-35-turbo-0125` - GPT-3.5 Turbo
- `gpt-4-32k` - GPT-4 with 32k context window

The deployment ID must match a deployment in your Azure OpenAI resource.

## Testing the Integration

You can test the Azure OpenAI integration using the provided test scripts:

```bash
# Test Azure OpenAI directly
python crewai_app/tests/test_azure_openai.py

# Test OpenRouter directly
python crewai_app/tests/test_openrouter.py

# Test the integration with CrewAI
python crewai_app/tests/test_crewai_integration.py
```

## Switching Between Providers

You can easily switch between OpenRouter and Azure OpenAI by changing the `LLM_PROVIDER` environment variable:

- For OpenRouter: `LLM_PROVIDER=openrouter`
- For Azure OpenAI: `LLM_PROVIDER=azure`

Make sure you have the appropriate API keys set for the provider you're using.

### OpenRouter Configuration

For OpenRouter, you can set the following environment variables:

```bash
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your-api-key
OPENAI_API_BASE=https://openrouter.ai/api/v1  # Optional, this is the default
OPENROUTER_MODEL=openai/gpt-4o-mini  # Optional, this is the default
```

Note that OpenRouter model IDs follow the format `provider/model-name`, such as:
- `openai/gpt-4o-mini`
- `openai/gpt-4`
- `anthropic/claude-3.5-sonnet`

## API Key Compatibility

The system now automatically sets the `OPENAI_API_KEY` environment variable to the value of `OPENROUTER_API_KEY` when using OpenRouter. This ensures compatibility with libraries like LiteLLM that expect the standard OpenAI API key to be set:

```python
# Set OPENAI_API_KEY environment variable for LiteLLM compatibility
os.environ["OPENAI_API_KEY"] = api_key
```

## Troubleshooting

If you encounter issues with the Azure OpenAI integration, check the following:

1. Verify that your API key and endpoint are correct
2. Ensure that the deployment ID you're using exists in your Azure OpenAI resource
3. Check the logs for any error messages
4. Verify that you have the correct permissions to access the Azure OpenAI resource

### OpenRouter Integration

If you encounter an error like `Completions.create() got an unexpected keyword argument 'headers'` when using OpenRouter, make sure you're using the latest version of the code. We've updated the integration to use `default_headers` instead of `model_kwargs.headers` to fix compatibility issues with the latest OpenAI SDK.

If you see an error like `'openrouter/openai/gpt-4o-mini is not a valid model ID'`, make sure you're using the correct model ID format. OpenRouter model IDs should be in the format `provider/model-name` (e.g., `openai/gpt-4o-mini`), not `openrouter/provider/model-name`.

For more information about Azure OpenAI, refer to the [official documentation](https://learn.microsoft.com/en-us/fabric/data-science/ai-services/how-to-use-openai-sdk-synapse?tabs=python0). 