import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()


class MetabaseCSVUploader:
    """
    A class to handle CSV file uploads to Metabase tables.
    
    Supports both replace (overwrite) and append operations.
    """
    
    def __init__(self, base_url: str = None, api_key: str = None):
        """
        Initialize the Metabase CSV uploader.
        
        Args:
            base_url: Metabase instance URL (e.g., 'https://metabase.example.com')
                     If not provided, will read from METABASE_URL env variable
            api_key: Metabase API key
                    If not provided, will read from METABASE_API_KEY env variable
        """
        self.base_url = (base_url or os.getenv('METABASE_URL', '')).rstrip('/')
        self.api_key = api_key or os.getenv('METABASE_API_KEY')
        
        if not self.base_url:
            raise ValueError("Metabase URL must be provided or set in METABASE_URL env variable")
        if not self.api_key:
            raise ValueError("Metabase API key must be provided or set in METABASE_API_KEY env variable")
        
        self.headers = {
            'X-API-KEY': self.api_key
        }
    
    def replace_csv(self, table_id: int, csv_file_path: str) -> dict:
        """
        Replace (overwrite) a Metabase table with CSV data.
        
        Args:
            table_id: The ID of the Metabase table to replace
            csv_file_path: Path to the CSV file to upload
            
        Returns:
            dict: Response from the Metabase API
            
        Raises:
            FileNotFoundError: If the CSV file doesn't exist
            requests.HTTPError: If the API request fails
        """
        csv_path = Path(csv_file_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        url = f"{self.base_url}/api/table/{table_id}/replace-csv"
        
        with open(csv_path, 'rb') as f:
            files = {
                'file': (csv_path.name, f, 'text/csv')
            }
            response = requests.post(url, headers=self.headers, files=files)
        
        response.raise_for_status()
        return response.json() if response.content else {"status": "success"}
    
    def append_csv(self, table_id: int, csv_file_path: str) -> dict:
        """
        Append CSV data to an existing Metabase table.
        
        Args:
            table_id: The ID of the Metabase table to append to
            csv_file_path: Path to the CSV file to upload
            
        Returns:
            dict: Response from the Metabase API
            
        Raises:
            FileNotFoundError: If the CSV file doesn't exist
            requests.HTTPError: If the API request fails
        """
        csv_path = Path(csv_file_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        url = f"{self.base_url}/api/table/{table_id}/append-csv"
        
        with open(csv_path, 'rb') as f:
            files = {
                'file': (csv_path.name, f, 'text/csv')
            }
            response = requests.post(url, headers=self.headers, files=files)
        
        response.raise_for_status()
        return response.json() if response.content else {"status": "success"}


def main():
    """
    Example usage of the MetabaseCSVUploader class.
    """
    # Initialize the uploader
    uploader = MetabaseCSVUploader()
    
    # Example: Replace table data
    table_id = 2179  # Replace with your actual table ID
    csv_file = "/Users/strider/Zamp/GitHub/special_projects/helpscout_tickets_agent/filing_reference_tbl.csv"
    
    try:
        result = uploader.replace_csv(table_id, csv_file)
        print(f"Successfully replaced table {table_id} with {csv_file}")
        print(f"Response: {result}")
    except Exception as e:
        print(f"Error replacing CSV: {e}")
    
    # Example: Append to table
    # try:
    #     result = uploader.append_csv(table_id, csv_file)
    #     print(f"Successfully appended {csv_file} to table {table_id}")
    #     print(f"Response: {result}")
    # except Exception as e:
    #     print(f"Error appending CSV: {e}")
    
    print("MetabaseCSVUploader initialized. Uncomment examples in main() to use.")


if __name__ == "__main__":
    main()
