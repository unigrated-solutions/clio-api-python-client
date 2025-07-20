import pandas as pd

try:
    # Try the installed package (preferred)
    from clio_manage_python_client import Clio_Manage
except ImportError:
    # Fallback: add local path (assumes script is in project_root/example_scripts/)
    import sys
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))

    from clio_manage_python_client import Clio_Manage


def process_file(file_path, client):
    # Read the file and ensure all columns are treated as strings to avoid unexpected data types
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path, dtype=str)
    elif file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path, dtype=str)
    else:
        raise ValueError("Unsupported file format. Use CSV or Excel.")

    # Ensure required columns exist
    required_columns = {'name', 'parent_type', 'field_type'}
    if not required_columns.issubset(df.columns):
        missing_cols = required_columns - set(df.columns)
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Function to normalize boolean values (returns None if the value should be omitted)
    def normalize_boolean(value):
        if pd.isna(value) or value in [None, "", "nan", "NaN"]:  # Handle NaN or empty values
            return None  # Do not include in API call
        if isinstance(value, bool):  # Already a boolean
            return value
        if isinstance(value, (int, float)):  # Convert numbers (1 → True, 0 → False)
            return bool(value)
        if isinstance(value, str):  # Convert string representations
            value = value.strip().lower()
            if value in {"true", "yes", "1"}:
                return True
            elif value in {"false", "no", "0"}:
                return False
        return None  # Exclude if unrecognized

    # Iterate through each row and make API calls
    responses = []
    for _, row in df.iterrows():
        try:
            # Construct API payload dynamically (include only required fields)
            payload = {
                "name": row["name"],
                "parent_type": row["parent_type"],
                "field_type": row["field_type"]
            }

            # Process `default` and `required` only if they exist in the file and are not empty
            if "default" in df.columns:
                default_value = normalize_boolean(row.get("default"))
                if default_value is not None:
                    payload["default"] = default_value  # Add only if valid

            if "required" in df.columns:
                required_value = normalize_boolean(row.get("required"))
                if required_value is not None:
                    payload["required"] = required_value  # Add only if valid

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
    client = Clio_Manage(access_token=access_token, store_responses=False)
    try:
        responses = process_file(file_path, client)
        print(responses)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        if client:
            client.shutdown() 
        print("Client shutdown completed.")
