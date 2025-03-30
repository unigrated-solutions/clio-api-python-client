import asyncio
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from client import Client  # Import your Client class

async def main():
    token = "CHANGEME"
    client = Client(access_token=token, store_responses=False, async_requests=True)
    
    try:
        
        response = await client.post.custom_fields(name="Test Field1", field_type="numERic", parent_type="mAtTeR", fields='all')
        print(json.dumps(response, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if client:
            await client.shutdown() 
        print("Client shutdown completed.")

# Run the async test
if __name__ == "__main__":
    asyncio.run(main())