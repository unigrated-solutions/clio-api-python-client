import pandas as pd
from client import Client

def process_file(file_path, client):
    # Read the file and ensure all columns are treated as strings
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path, dtype=str)  # Read all as strings
    elif file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path, dtype=str)
    else:
        raise ValueError("Unsupported file format. Use CSV or Excel.")

    # Ensure required columns exist
    required_columns = {'name', 'parent_type', 'field_type'}
    if not required_columns.issubset(df.columns):
        missing_cols = required_columns - set(df.columns)
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Function to normalize boolean values
    def normalize_boolean(value):
        if pd.isna(value) or value in [None, "", "nan", "NaN"]:  # Handle NaN or empty values
            return None  # Return None to indicate omission from API call
        if isinstance(value, bool):  # Already a boolean
            return value
        if isinstance(value, (int, float)):  # Handle numbers
            return bool(value)
        if isinstance(value, str):  # Normalize string representations
            return value.strip().lower() in {"true", "yes", "1"}
        return None  # Default to None for unrecognized values

    # Iterate through each row and make API calls
    responses = []
    for _, row in df.iterrows():
        try:
            # Construct API payload dynamically
            payload = {
                "name": row["name"],
                "parent_type": row["parent_type"],
                "field_type": row["field_type"]
            }

            # Process `default` and `required`, adding them only if they are not empty
            default_value = normalize_boolean(row.get("default"))
            required_value = normalize_boolean(row.get("required"))

            if default_value is not None:
                payload["displayed"] = default_value  #### THE API USES displayed in the request but whats most are used to seeing under the "Default" column
            if required_value is not None:
                payload["required"] = required_value  # Add only if not empty

            # Make the API request
            response = client.post.custom_fields(**payload)
            responses.append(response)
        except Exception as e:
            print(f"Error processing row {row.to_dict()}: {e}")

    return responses

if __name__ == "__main__":
    
    '''
    1) Create an excel or csv file with the following headers: name, parent_type, field_type, default, required
    2) parent types allowed: Matter, Contact
    3) field_type: checkbox, contact, currency, date, time, email, matter, numeric, text_area, text_line, url

    '''
    access_token = "CHANGEME"
    file_path = "CHANGEME"
    client = Client(access_token=access_token)
    try:
        responses = process_file(file_path, client)
        print(responses)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if client:
            client.shutdown() 
        print("Client shutdown completed.")
