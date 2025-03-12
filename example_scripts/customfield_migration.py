"""
Custom Fields Migration Script
=================================

This script allows users to **import and export custom fields** using the Clio API client.

Features:
- **Import custom fields** from an Excel (.xlsx) or CSV (.csv) file.
- **Export existing custom fields** from the API to an Excel file.
- **Handles errors gracefully** and logs failed imports to `failed_imports.txt`.
- **Skips picklist fields** (as they cannot be imported).
- **Skips deleted fields** (if the 'deleted' column is present and marked as True).
- **Marks picklist and deleted fields in the exported file** so users are aware they won't migrate.

Usage:
------
This script is intended to be run via the command line.

**Basic Commands:**
-------------------
1. **Export Custom Fields (default filename: `custom_fields.xlsx`):**
   ```sh
   python example_scripts/customfield_migration.py --token EXPORT_ACCOUNT_ACCESS_TOKEN --export

2. **Import Custom Fields (default filename: `custom_fields.xlsx`):**
   ```sh
   python example_scripts/customfield_migration.py --token IMPORT_ACCOUNT_ACCESS_TOKEN --import a_different_file_path.xlsx
   
"""

import sys
import os
import argparse
import pandas as pd

# Get the absolute path of the script file
script_dir = os.path.dirname(os.path.abspath(__file__))
cwd = os.getcwd()

# Modify sys.path only if necessary
if script_dir != cwd:
    sys.path.append(os.path.abspath(os.path.join(script_dir, "..")))

# Import Client from the parent directory
try:
    from client import Client
except ImportError:
    raise ImportError("Could not find 'client.py'. Ensure it exists in the parent directory.")

def get_output_filename(base_filename):
    """Ensures the output filename does not overwrite an existing file by appending a count."""
    if not os.path.exists(base_filename):
        return base_filename

    file_root, file_ext = os.path.splitext(base_filename)
    counter = 1

    while True:
        new_filename = f"{file_root}({counter}){file_ext}"
        if not os.path.exists(new_filename):
            return new_filename
        counter += 1
        
def normalize_boolean(value):
    """Converts values to boolean or None."""
    if pd.isna(value) or value in {None, "", "nan", "NaN"}:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        value = value.strip().lower()
        return {"true": True, "yes": True, "1": True, "false": False, "no": False, "0": False}.get(value, None)
    return None  

def import_custom_fields(file_path, client):
    """Imports custom fields from an Excel/CSV file and makes API calls to update them."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")

    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, dtype=str)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, dtype=str)
        else:
            raise ValueError("Unsupported file format. Use CSV or Excel.")
    except Exception as e:
        raise RuntimeError(f"Error reading the file: {e}")

    required_columns = {'name', 'parent_type', 'field_type'}
    missing_cols = required_columns - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Handling both "default" and "displayed" as inputs for "displayed"
    column_mapping = {"default": "displayed", "required": "required"}
    
    if "displayed" in df.columns:
        column_mapping["displayed"] = "displayed"

    failed_imports = []
    responses = []

    for index, row in df.iterrows():
        try:
            # Skip "picklist" fields since they cannot be imported
            if row["field_type"].strip().lower() == "picklist":
                print(f"Skipping 'picklist' field at row {index}: {row['name']}")
                continue

            # Skip "deleted" fields if the column exists and is marked as True
            if "deleted" in df.columns:
                deleted_value = normalize_boolean(row.get("deleted"))
                if deleted_value is True:
                    print(f"Skipping deleted field at row {index}: {row['name']}")
                    continue

            payload = {
                "name": row["name"].strip(),
                "parent_type": row["parent_type"].strip(),
                "field_type": row["field_type"].strip()
            }

            for col, payload_key in column_mapping.items():
                if col in df.columns:
                    value = normalize_boolean(row.get(col))
                    if value is not None:
                        payload[payload_key] = value

            response = client.post.custom_fields(**payload)
            responses.append(response)

        except Exception as e:
            error_msg = f"Failed to import row {index} ({row.to_dict()}): {e}"
            print(error_msg)
            failed_imports.append(error_msg)

    # Save failed imports to a file
    if failed_imports:
        with open("failed_imports.txt", "w") as f:
            f.write("\n".join(failed_imports))
        print(f"Import completed with errors. See 'failed_imports.txt' for details.")
    else:
        print("Import completed successfully.")

    return responses

def export_custom_fields(client, output_file="custom_fields.xlsx"):
    """Fetches all custom fields and exports them to an Excel file, ensuring no overwrites."""
    try:
        response = client.all.custom_fields(fields="all")  # Keeping the correct API call
        if "data" not in response or not isinstance(response["data"], list):
            raise ValueError("Invalid API response format.")

        columns = ["id", "etag", "created_at", "updated_at", "name", "parent_type", 
                   "field_type", "displayed", "deleted", "required", "display_order"]

        data = [{col: item.get(col, "") for col in columns} for item in response["data"]]
        df = pd.DataFrame(data)

        # Highlight "picklist" fields and "deleted" fields by adding a warning column
        def warning_message(row):
            if row["field_type"].lower() == "picklist":
                return "Picklist - Cannot currently be imported"
            if "deleted" in row and normalize_boolean(row["deleted"]) is True:
                return "Deleted field - will not be imported"
            return ""

        df["warning"] = df.apply(warning_message, axis=1)

        # Ensure we do not overwrite an existing file
        output_filename = get_output_filename(output_file)

        df.to_excel(output_filename, index=False)

        print(f"Custom fields exported to {output_filename}. 'Picklist' and 'Deleted' fields are marked.")

    except Exception as e:
        print(f"Failed to export custom fields: {e}")

def main():
    parser = argparse.ArgumentParser(description="Manage custom fields with a client API.")
    
    parser.add_argument("--token", type=str, required=True, help="API access token.")
    
    parser.add_argument("--import", dest="import_file", type=str, nargs="?", const="custom_fields.xlsx", 
                        help="Import custom fields from an XLSX or CSV file (default: custom_fields.xlsx).")
    
    parser.add_argument("--export", dest="export_file", type=str, nargs="?", const="custom_fields.xlsx", 
                        help="Export custom fields to an XLSX file (default: custom_fields.xlsx).")
    
    args = parser.parse_args()

    # Initialize Client
    client = Client(access_token=args.token, store_responses=False)

    try:
        if args.export_file:
            export_custom_fields(client, args.export_file)
        if args.import_file:
            responses = import_custom_fields(args.import_file, client)
            print("API Responses:", responses)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.shutdown()
        print("Client shutdown completed.")

if __name__ == "__main__":
    main()