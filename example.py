import json
from datetime import datetime, timedelta, date

from clio_manage_python_client import Clio_Manage

# Example usage
if __name__ == "__main__":
    '''
    Required Permissions to run examples below:
    Read: Api, Calendars, Contacts, Custom Fields, Documents, General, Matters, Users
    '''
    token = "ACCESS TOKEN"
    client = Clio_Manage(access_token=token, store_responses=True)
    try:

        random_id = client.utils.export.get_random_id(client.get.matters(limit=100, fields="id"))
        
        response = client.get.matters(id=random_id, fields="id,description,location,client{id,name}")
        print(json.dumps(response, indent=2))
        
        response = client.get.matters.related_contacts(id=random_id, fields="first_name,last_name,is_matter_client,relationship{description}")
        print(json.dumps(response, indent=2))
        
        response = client.get.matters.contacts(id=random_id, fields="first_name,last_name,is_client,relationship{description}")
        print(json.dumps(response, indent=2))
        
        one_year_ago = date.today() - timedelta(days=365)
        response = client.all.matters(limit=200, open_date__= f'>={one_year_ago}', order="open_date(asc)", fields="id,display_number,custom_number,open_date,description,location,client_reference,has_tasks,client{name},practice_area{name,category},responsible_attorney{name}")
        client.utils.export.save_to_xlsx(response)
        
        client.utils.export.save_to_xlsx(client.all.calendar_entries(fields="start_at,end_at,all_day,location,description,summary,attendees{name}", from_=datetime.now(), to=client.utils.time.end_of_the_month()),"calendar_spreadsheet.xlsx")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if client:
            client.shutdown() 
        print("Client shutdown completed.")