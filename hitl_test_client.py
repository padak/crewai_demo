import asyncio
import aiohttp
import json
import time
import argparse

async def test_hitl_workflow(server_url, topic, approve=False, feedback=None, webhook_url=None):
    """
    Test the Human-in-the-Loop workflow
    
    Args:
        server_url: Base URL of the API server
        topic: Topic for content creation
        approve: Whether to approve the content or provide feedback
        feedback: Feedback to provide if not approving
        webhook_url: URL to send webhook notifications to
    """
    async with aiohttp.ClientSession() as session:
        # Step 1: Start a content creation job with HITL
        data = {
            "function": "create_content_with_hitl",
            "args": [topic],
            "kwargs": {}
        }
        
        # Add webhook URL if provided
        if webhook_url:
            data["webhook_url"] = webhook_url
            
        print(f"\n=== Starting Content Creation with HITL for topic: {topic} ===")
        print("Sending request...")
        
        async with session.post(f'{server_url}/invoke', json=data) as response:
            result = await response.json()
            print("\nJob started:")
            print(json.dumps(result, indent=2))
            
            # Get the job ID
            job_id = result.get("job_id")
            if not job_id:
                print("Error: No job ID returned")
                return
        
        # Step 2: Poll for job status until it's pending approval
        print("\n=== Polling for Job Status ===")
        job_status = await poll_until_pending_approval(session, server_url, job_id)
        
        if not job_status or job_status.get("status") != "pending_approval":
            print(f"Job did not reach pending_approval state. Current status: {job_status.get('status', 'unknown')}")
            return
        
        # Step 3: Display the content for review
        content = job_status.get("result", {}).get("result", {}).get("content", "")
        print("\n=== Content Ready for Review ===")
        print("-" * 80)
        print(content[:500] + "..." if len(content) > 500 else content)
        print("-" * 80)
        
        # Step 4: Provide feedback or approval
        if approve:
            feedback_data = {
                "feedback": "Content approved as is.",
                "approved": True
            }
            print("\n=== Approving Content ===")
        else:
            if not feedback:
                feedback = "Please make the content more concise and add more specific examples."
            feedback_data = {
                "feedback": feedback,
                "approved": False
            }
            print(f"\n=== Providing Feedback ===\n{feedback}")
        
        async with session.post(f'{server_url}/job/{job_id}/feedback', json=feedback_data) as response:
            feedback_result = await response.json()
            print("\nFeedback submitted:")
            print(json.dumps(feedback_result, indent=2))
        
        # Step 5: If not approved, poll for the revised content
        if not approve:
            print("\n=== Polling for Revised Content ===")
            await poll_until_completed(session, server_url, job_id)

async def poll_until_pending_approval(session, server_url, job_id, max_attempts=30, delay=5):
    """Poll until job reaches pending_approval status"""
    for attempt in range(1, max_attempts + 1):
        async with session.get(f'{server_url}/job/{job_id}') as response:
            job_status = await response.json()
            status = job_status.get("status")
            
            print(f"Attempt {attempt}: Status = {status}")
            
            if status == "pending_approval":
                print("\nJob is ready for human review!")
                return job_status
            elif status == "error":
                print("\nJob failed with error:")
                print(job_status.get("error", "Unknown error"))
                return None
            elif status == "processing" or status == "queued":
                print(f"Job still {status}... waiting {delay} seconds")
                await asyncio.sleep(delay)
            else:
                print(f"Unexpected status: {status}")
                return job_status
    
    print("Maximum polling attempts reached.")
    return None

async def poll_until_completed(session, server_url, job_id, max_attempts=30, delay=5):
    """Poll until job reaches completed status"""
    for attempt in range(1, max_attempts + 1):
        async with session.get(f'{server_url}/job/{job_id}') as response:
            job_status = await response.json()
            status = job_status.get("status")
            
            print(f"Attempt {attempt}: Status = {status}")
            
            if status == "completed":
                print("\nJob completed successfully!")
                content = job_status.get("result", {}).get("content", "")
                print("\n=== Revised Content ===")
                print("-" * 80)
                print(content[:500] + "..." if len(content) > 500 else content)
                print("-" * 80)
                return job_status
            elif status == "error":
                print("\nJob failed with error:")
                print(job_status.get("error", "Unknown error"))
                return None
            elif status == "processing" or status == "queued":
                print(f"Job still {status}... waiting {delay} seconds")
                await asyncio.sleep(delay)
            else:
                print(f"Unexpected status: {status}")
                return job_status
    
    print("Maximum polling attempts reached.")
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the HITL workflow")
    parser.add_argument("--url", default="http://localhost:8888", help="API server URL")
    parser.add_argument("--topic", default="Artificial Intelligence Ethics", help="Topic for content creation")
    parser.add_argument("--approve", action="store_true", help="Approve the content instead of providing feedback")
    parser.add_argument("--feedback", help="Feedback to provide if not approving")
    parser.add_argument("--webhook-url", help="URL to send webhook notifications to")
    
    args = parser.parse_args()
    
    print("Starting HITL test client...")
    asyncio.run(test_hitl_workflow(args.url, args.topic, args.approve, args.feedback, args.webhook_url)) 