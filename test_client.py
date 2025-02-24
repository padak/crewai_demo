import asyncio
import aiohttp
import json

async def test_http_endpoints():
    async with aiohttp.ClientSession() as session:
        # Test root endpoint
        async with session.get('http://localhost:8888/') as response:
            print("\n=== Testing Root Endpoint ===")
            print(await response.json())

        # Test health endpoint
        async with session.get('http://localhost:8888/health') as response:
            print("\n=== Testing Health Endpoint ===")
            print(await response.json())

        # Test list-functions endpoint
        async with session.get('http://localhost:8888/list-functions') as response:
            print("\n=== Testing List Functions ===")
            print(await response.json())

        # Test invoke endpoint with create_content
        data = {
            "function": "create_content",
            "args": ["Test topic about AI"],
            "kwargs": {}
        }
        print("\n=== Testing Create Content ===")
        print("Sending request... (this might take a while)")
        async with session.post('http://localhost:8888/invoke', json=data) as response:
            result = await response.json()
            print("\nResponse received:")
            print(json.dumps(result, indent=2))

if __name__ == "__main__":
    print("Starting test client...")
    asyncio.run(test_http_endpoints()) 