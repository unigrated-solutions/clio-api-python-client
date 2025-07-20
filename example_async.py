import asyncio
import json
from datetime import datetime, timedelta, date

from clio_manage_python_client import Clio_Manage


async def main():
    '''
    Required Permissions to run examples below:
    Read: Api, Calendars, Contacts, Custom Fields, Documents, General, Matters, Users
    '''
    token = "ACCESS TOKEN"
    client = Clio_Manage(access_token=token, store_responses=True, async_requests=True)

    try:
        # Use utility to pick a random ID from recent matters
        random_id = client.utils.export.get_random_id(
            await client.get.matters(limit=100, fields="id")
        )

        # Fetch a specific matter
        response = await client.get.matters(
            id=random_id,
            fields="id,description,location,client{id,name}"
        )
        print(json.dumps(response, indent=2))

        # Related contacts
        response = await client.get.matters.related_contacts(
            id=random_id,
            fields="first_name,last_name,is_matter_client,relationship{description}"
        )
        print(json.dumps(response, indent=2))

        # Matter contacts
        response = await client.get.matters.contacts(
            id=random_id,
            fields="first_name,last_name,is_client,relationship{description}"
        )
        print(json.dumps(response, indent=2))

        # Export recent matters
        one_year_ago = date.today() - timedelta(days=365)
        response = await client.all.matters(
            limit=200,
            open_date__=f'>={one_year_ago}',
            order="open_date(asc)",
            fields="id,display_number,custom_number,open_date,description,location,client_reference,has_tasks,client{name},practice_area{name,category},responsible_attorney{name}"
        )
        client.utils.export.save_to_xlsx(response, "recent_matters.xlsx")

        # Export calendar entries
        response = await client.all.calendar_entries(
            fields="start_at,end_at,all_day,location,description,summary,attendees{name}",
            from_=datetime.now(),
            to=client.utils.time.end_of_the_month()
        )
        client.utils.export.save_to_xlsx(response, "calendar_entries.xlsx")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        await client.shutdown()
        print("Client shutdown completed.")


if __name__ == "__main__":
    asyncio.run(main())
