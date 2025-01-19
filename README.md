
# Advanced API Client for Clio

This advanced API client is designed to interact with the Clio API, providing robust handling for HTTP request methods, query parameters, payload validation, and dynamic endpoint management.

## Key Features

1. **Dynamic Endpoint Management**:
   - Dynamically initializes and manages endpoints using metadata from the `models.endpoints` module.
   - Supports operations like `index`, `show`, `post`, `patch`, `delete` as well as sub-methods for relational endpoints (Explained Below)
   - Endpoints that return content can use the `download` method. Output path can be provided in the call or set within the client

2. **Integrated Query Parameter and Payload Handling**:
   - Automatically validates, converts, and processes query parameters and payload data.
   - Ensures type safety and required field validation for all inputs.
   - Query parameters are processed first and removed from `kwargs`. Remaining `kwargs` are processed for payload data.

3. **Pagination Support**:
   - Handles paginated responses seamlessly when using the `all` method.
   - Automatically appends results from all pages.

4. **Reserved Keywords and Parameter Mappings**:
   - Handles reserved keywords and endpoint-specific parameters via a `mappings` dictionary.
   - Reserved keywords such as `from` and `X-API-VERSION` are mapped to their correct representations (e.g., `from_` to `from`).
   - Parameters like `matter_id` and `id` are interchangeable, ensuring ease of use for endpoints that deviate from the general schema.

5. **Dynamic Endpoint Resolution**:
   - Determines whether to call the `index` or `show` endpoint based on the presence of `id` in `kwargs`.
   - For example:
     - `client.get.matters(id=123)` calls the `show` endpoint.
     - `client.get.matters(limit=10)` calls the `index` endpoint.

6. **Rate Limiting**:
   - Enforces rate limits using the `RateMonitor` class to ensure compliance with API restrictions.

7. **Error Reporting**:
   - Provides detailed validation error messages when inputs do not meet the expected types or requirements.

---

## Reserved Keywords and Mapping

The client automatically handles reserved keywords and non-standard endpoint parameters through a predefined `mappings` dictionary. This ensures compatibility and ease of use for all endpoints.

### Example Mappings

```python
mappings = {
    "X_API_VERSION": "X-API-VERSION",
    "from_": "from", 
    "ids__": "ids",
    "jurisdiction__id": "jurisdiction[id]",
    "service_type__id": "service_type[id]",
    "trigger__id": "trigger[id]",
}
```

### Handling Non-Standard Endpoints

**Example Endpoint**:
- **`https://app.clio.com/api/v4/matters/{matter_id}/client.json`**
- **`https://app.clio.com/api/v4/matters/{id}.json`**

Both `matter_id` and `id` can be used interchangeably. The client automatically maps `matter_id` to `id` for consistency.

## Example Usage

```python
# Calls the 'show' endpoint for a specific matter
response = client.get.matters(id=123)

# Calls the 'client' relation endpoint for a specific matter
response = client.get.matters.client(matter_id=123)

# Calls the 'client' relation endpoint for a specific matter
response = client.get.matters.client(id=123)
```

## Arrays(Needs more testing):
- **Can be provided using by including a double underscore**
- **Any text after the underscores get converted into a query parameter keyword**
   - **`ids__ = [123,456,789]` gets converted to `ids[]=123&ids[]=456&ids[]=789`**
   - **`jurisdiction__id = 123` gets converted to `jurisdiction[id]=123`**

---

## Usage

### Initialization

```python
from client import Client

client = Client(access_token="your_access_token")
```

### Single Request Example

```python
response = client.get.matters(fields="id", limit=10)
print(response)
```

### Fetch All Paginated Results

```python
response_all = client.all.matters(fields="id,name")
print(f"Total items retrieved: {len(response_all['data'])}")
```

### Relations Example

```python
related_contacts = client.get.matters.related_contacts(id=12345, fields="id,name")
print(related_contacts)
```

---

## Internal Design

### Endpoint Resolution

- The `show` endpoint is prioritized if `id` is present in the `kwargs`.
- The `index` endpoint is called if `id` is not provided.

### `_request_handler`

Handles requests, including:
- Pagination support.
- Query parameter and payload validation.
- Dynamic path formatting with provided arguments.

---

## Debugging

Detailed logs are provided to help debug requests:
- URL being called.
- Parameters and payloads.
- Pagination information (`page_token`).

---

## Requirements

- Python 3.7+
- `requests` library

---

## License

This project is licensed under the MIT License.
