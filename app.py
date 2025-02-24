from datetime import datetime
import importlib.util
import logging
import os
import sys

import tomli
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="Content Orchestrator")

# Add CORS middleware with security settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # In production, specify your actual domains
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load secrets from .streamlit/secrets.toml
try:
    with open(".streamlit/secrets.toml", "rb") as f:
        secrets = tomli.load(f)
        for key, value in secrets.items():
            if isinstance(value, str):
                os.environ[key] = value
        logger.info("Successfully loaded secrets from .streamlit/secrets.toml")
except Exception as e:
    logger.warning(f"Could not load secrets: {e}")

# Import the user's script
script_path = os.getenv("DATA_APP_ENTRYPOINT", "user_script.py")
try:
    spec = importlib.util.spec_from_file_location("user_script", script_path)
    user_module = importlib.util.module_from_spec(spec)
    sys.modules["user_script"] = user_module
    spec.loader.exec_module(user_module)
    logger.info(f"Successfully loaded user script from {script_path}")
except Exception as e:
    logger.error(f"Failed to load user script: {e}")
    raise


@app.get("/")
async def root():
    """Root endpoint with application status"""
    return {
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for the proxy"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "module_loaded": user_module is not None,
    }


@app.post("/invoke")
async def invoke_function(request: Request):
    try:
        data = await request.json()
        function_name = data.get("function")
        args = data.get("args", [])
        kwargs = data.get("kwargs", {})

        if not hasattr(user_module, function_name):
            return JSONResponse(
                status_code=404,
                content={"error": f"Function {function_name} not found"},
            )

        func = getattr(user_module, function_name)
        logger.info(f"Invoking function: {function_name}")
        result = func(*args, **kwargs)
        return {"result": result}
    except Exception as e:
        logger.error(f"Error invoking function: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/list-functions")
async def list_functions():
    """List available functions in the user module"""
    try:
        functions = [
            name
            for name, obj in vars(user_module).items()
            if callable(obj) and not name.startswith("_")
        ]
        return {"functions": functions}
    except Exception as e:
        logger.error(f"Error listing functions: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})
