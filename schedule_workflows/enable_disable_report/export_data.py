
import os
import csv
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

METABASE_QUESTION_ID = "10100"

class MetabaseClient:
    """Simplified Metabase API client."""
    
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers['X-API-KEY'] = api_key
    
    def export_to_csv(self, question_id, output_file):
        """Execute query and export to CSV."""
        response = self.session.post(f"{self.base_url}/api/card/{question_id}/query")
        response.raise_for_status()
        
        data = response.json()['data']
        rows = data['rows']
        cols = [col.get('display_name', col.get('name', f'col_{i}')) 
                for i, col in enumerate(data['cols'])]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            writer.writerows(rows)
        
        return len(rows)


def main():
    load_dotenv()
    
    # Get required config
    url = os.getenv('METABASE_URL')
    question_id = METABASE_QUESTION_ID
    api_key = os.getenv('METABASE_API_KEY')
    
    # Validate
    if not url or not question_id or not api_key:
        sys.exit("Error: METABASE_URL, METABASE_QUESTION_ID, and METABASE_API_KEY required in .env")
    
    try:
        # Connect and export
        client = MetabaseClient(url, api_key)
        output_file = f"data/EnabledDisabledReport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        row_count = client.export_to_csv(int(question_id), output_file)
        print(f"✓ Exported {row_count} rows to {output_file}")
    except Exception as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()