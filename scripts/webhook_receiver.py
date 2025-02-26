from fastapi import FastAPI, Request
import uvicorn
import json
from datetime import datetime
import argparse

app = FastAPI(title="Webhook Receiver")

# Store received webhooks
webhooks = []

@app.get("/")
async def root():
    """List all received webhooks"""
    return {"webhooks": webhooks}

@app.post("/webhook")
async def receive_webhook(request: Request):
    """Receive and store webhook data"""
    try:
        data = await request.json()
        webhook_entry = {
            "received_at": datetime.now().isoformat(),
            "data": data
        }
        webhooks.append(webhook_entry)
        print(f"\n=== Webhook Received at {webhook_entry['received_at']} ===")
        print(json.dumps(data, indent=2))
        return {"status": "success", "message": "Webhook received"}
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/clear")
async def clear_webhooks():
    """Clear all stored webhooks"""
    webhooks.clear()
    return {"status": "success", "message": "All webhooks cleared"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a webhook receiver for testing")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8889, help="Port to bind to")
    
    args = parser.parse_args()
    
    print(f"Starting webhook receiver on http://{args.host}:{args.port}")
    print(f"Webhook URL: http://{args.host}:{args.port}/webhook")
    uvicorn.run(app, host=args.host, port=args.port) 