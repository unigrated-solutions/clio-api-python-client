import json
import requests
import time
import re
import threading

from datetime import datetime, timedelta, date
from functools import wraps

import configs
from classes.request_methods import Get, Put, Post,Patch,Delete,Download, All
from utils.export import save_to_xlsx, get_random_id
from utils.time import end_of_the_month


BASE_URL = "https://app.clio.com/api/v4"

class RateMonitor:
    def __init__(self, default_limit=60):

        self.default_limit = default_limit
        self.limits = {} 
        self.lock = threading.Lock()
        self.call_times = {} 

    def extract_base_endpoint(self, url: str) -> str:
        """
        Extracts the base endpoint from a given URL or endpoint string.
        """
        if url.startswith(BASE_URL):
            url = url[len(BASE_URL):]

        url = url.lstrip('/').rstrip('/')

        url = re.sub(r"/\{[^/]*\}", "", url)  # Remove placeholders like /{id}
        url = re.sub(r"/\d+", "", url)       # Remove numeric IDs like /12345

        # Step 4: Normalize the endpoint to the base path
        base_endpoint = url.split('/')[0] if url else ""
        base_endpoint = base_endpoint.replace(".json","")
        return base_endpoint
    
    def update_rate_limits(self, endpoint, response_headers):
        """
        Update the rate limit details for an endpoint based on response headers.
        """
        with self.lock:
            endpoint = self.extract_base_endpoint(endpoint)
            
            if endpoint not in self.limits:
                self.limits[endpoint] = {
                    "limit": self.default_limit,
                    "remaining": self.default_limit,
                    "reset": time.time() + 60, 
                    "retry_after": None
                }
            reset_timestamp = time.time()
            
            # Update from headers if available
            if "X-RateLimit-Limit" in response_headers:
                self.limits[endpoint]["limit"] = int(response_headers["X-RateLimit-Limit"])
            if "X-RateLimit-Remaining" in response_headers:
                self.limits[endpoint]["remaining"] = int(response_headers["X-RateLimit-Remaining"])
            if "X-RateLimit-Reset" in response_headers:
                reset_timestamp = int(response_headers["X-RateLimit-Reset"])
                self.limits[endpoint]["reset"] = reset_timestamp
            if "Retry-After" in response_headers:
                self.limits[endpoint]["retry_after"] = int(response_headers["Retry-After"])
            
            print(f"Rate limit for {endpoint}: {self.limits[endpoint]}")
            print(f"Limit resets in {int(reset_timestamp - time.time())} seconds")
            
    def __call__(self, endpoint):
        """
        Decorator to enforce the rate limit on a function for a specific endpoint.
        """
        def decorator(func):
            base_endpoint = self.extract_base_endpoint(endpoint)
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.lock:
                    if base_endpoint not in self.limits:
                        self.limits[base_endpoint] = {
                            "limit": self.default_limit,
                            "remaining": self.default_limit,
                            "reset": time.time() + 60,
                            "retry_after": None
                        }

                    limit_details = self.limits[base_endpoint]
                    current_time = time.time()

                    # Remove timestamps older than 60 seconds
                    self.call_times[base_endpoint] = [
                        t for t in self.call_times.get(base_endpoint, []) if current_time - t < 60
                    ]

                    if len(self.call_times[base_endpoint]) >= limit_details["limit"]:
                        # Calculate wait time based on reset time or first call
                        if current_time < limit_details["reset"]:
                            wait_time = limit_details["reset"] - current_time
                        else:
                            wait_time = 60 - (current_time - self.call_times[base_endpoint][0])
                        print(f"Rate limit exceeded for {base_endpoint}. Waiting for {wait_time:.2f} seconds.")
                        time.sleep(wait_time)

                    # Record the current call's timestamp
                    self.call_times[base_endpoint].append(time.time())
                    limit_details["remaining"] = max(0, limit_details["remaining"] - 1)

                return func(*args, **kwargs)

            return wrapper
        return decorator
    
class Client:
    def __init__(self, access_token, default_rate_limit=60):
        self.base_url = BASE_URL
        self.access_token = access_token
        self.rate_limiter = RateMonitor(default_limit=default_rate_limit)  # Attach rate limiter

        # List of HTTP methods and their corresponding handler classes
        self.request_methods = configs.request_methods
        request_handler_classes = {
            "get": Get,
            "put": Put,
            "post": Post,
            "patch": Patch,
            "delete": Delete,
            "download": Download,
            "all": All  # Include the All class
        }

        # Dynamically initialize and set request handlers as attributes
        for method in self.request_methods:
            handler_class = request_handler_classes[method]
            setattr(self, method, handler_class(self.base_url, self._request_handler))

    def __getattr__(self, item: str):
        """
        Forward attribute access to the appropriate request type.
        """
        for method in self.request_methods:
            handler = getattr(self, method, None)
            if handler and hasattr(handler, item):
                return getattr(handler, item)
        raise AttributeError(f"'Client' object has no attribute '{item}'")
    
    def _make_request(self, url: str, method: str, params: dict = None, payload: dict = None, return_all=False):
        """
        Makes the actual HTTP request based on the method.
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        print(params)
        params = params or {}

        try:
            # Make the request
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=payload,
            )
            response.raise_for_status()
            return response.json(), response
        
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"HTTP request failed: {e}") from e

    def _request_handler(self, url: str, method: str, params: dict = None, payload: dict = None, return_all=False, **kwargs):
        """
        Handles requests, including support for paginated responses when return_all=True.
        """
        endpoint = url.split(BASE_URL)[-1].split("?")[0]  # Extract endpoint from URL
        params = params or {}

        @self.rate_limiter(endpoint)
        def make_request():
            try:
                if method == "DOWNLOAD":
                    response_obj = self._download_content(url, params)
                    self.rate_limiter.update_rate_limits(endpoint, response_obj.headers)
                    return response_obj

                if not return_all:
                    # Single request
                    response_json, response_obj = self._make_request(url, method, params, payload)
                    self.rate_limiter.update_rate_limits(endpoint, response_obj.headers)
                    return response_json

                # Paginated request
                all_results = []
                next_page_token = None

                while True:
                    
                    if next_page_token:
                        params["page_token"] = next_page_token

                    response_json, response_obj = self._make_request(url, method, params, payload)
                    self.rate_limiter.update_rate_limits(endpoint, response_obj.headers)

                    all_results.extend(response_json.get("data", []))

                    next_page_token = response_json.get("meta", {}).get("paging", {}).get("next_page_token")
                    if not next_page_token:
                        break

                return {"data": all_results}

            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"API request failed: {e}")

        return make_request()
    
    def _download_content(self, url: str, params: dict = None):
        """
        Makes the actual HTTP request based on the method.
        """

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/pdf",
            }
        try:
            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                raise requests.exceptions.RequestException(
                    f"Rate limited. Retry after {retry_after} seconds."
                )

            if response.status_code != 200:
                raise requests.exceptions.RequestException(f"HTTP {response.status_code}: {response.text}")

            return response
        
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"HTTP request failed: {e}") from e
        

# Example usage
if __name__ == "__main__":
    '''
    Required Permissions to run examples below:
    Read: Api, Calendars, Contacts, Custom Fields, Documents, General, Matters, Users
    '''
    token = "ACCESS_TOKEN"
    client = Client(access_token=token)
    
    random_id = get_random_id(client.get.matters(limit=100, fields="id"))
    
    response = client.get.matters(id=random_id, fields="id,description,location,client{id,name}")
    print(json.dumps(response, indent=2))
    
    response = client.get.matters.related_contacts(id=random_id, fields="first_name,last_name,is_matter_client,relationship{description}")
    print(json.dumps(response, indent=2))
    
    response = client.get.matters.contacts(id=random_id, fields="first_name,last_name,is_client,relationship{description}")
    print(json.dumps(response, indent=2))
    
    one_year_ago = date.today() - timedelta(days=365)
    response = client.all.matters(limit=200, open_date__= f'>={one_year_ago}', order="open_date(asc)", fields="id,display_number,custom_number,open_date,description,location,client_reference,has_tasks,client{name},practice_area{name,category},responsible_attorney{name}")
    save_to_xlsx(response)
    
    save_to_xlsx(client.all.calendar_entries(fields="start_at,end_at,all_day,location,description,summary,attendees{name}", from_=datetime.now(), to=end_of_the_month()),"calendar_spreadsheet.xlsx")
