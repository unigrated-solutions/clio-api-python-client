import asyncio
import json
from datetime import datetime, timedelta, date

from utils.export import save_to_xlsx, get_random_id
from utils.time import end_of_the_month

from client import Client  # Import your Client class

async def main():
    token = "Access Token"
    client = Client(access_token=token, store_responses=True, async_requests=True)
    
    try:
        random_id = get_random_id(client.get.matters(limit=100, fields="id"))
        
        response = await client.get.matters(id=random_id, fields="id,description,location,client{id,name}")
        print(json.dumps(response, indent=2))
        
        response = await client.get.matters.related_contacts(id=random_id, fields="first_name,last_name,is_matter_client,relationship{description}")
        print(json.dumps(response, indent=2))
        
        response = await client.get.matters.contacts(id=random_id, fields="first_name,last_name,is_client,relationship{description}")
        print(json.dumps(response, indent=2))
        
        one_year_ago = date.today() - timedelta(days=365)
        response = await client.all.matters(limit=200, open_date__= f'>={one_year_ago}', order="open_date(asc)", fields="id,display_number,custom_number,open_date,description,location,client_reference,has_tasks,client{name},practice_area{name,category},responsible_attorney{name}")
        save_to_xlsx(response)
        
    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if client:
            await client.shutdown() 
        print("Client shutdown completed.")

# Run the async test
if __name__ == "__main__":
    asyncio.run(main())