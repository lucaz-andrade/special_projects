
"""
Monthly Metabase Export Scheduler

Runs on the 1st of every month to:
1. Export Metabase query to CSV
2. Send CSV via email

Cron schedule: 0 9 1 * * (9 AM on the 1st of every month)
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Import from local modules
from export_data import MetabaseClient
from mailman import send_csv_email


def run_monthly_export():
    """Execute monthly export and email workflow."""
    load_dotenv()
    
    print(f"\n{'='*60}")
    print(f"Monthly Export Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Get config
    url = os.getenv('METABASE_URL')
    question_id = os.getenv('METABASE_QUESTION_ID')
    api_key = os.getenv('METABASE_API_KEY')
    
    # Validate
    if not url or not question_id or not api_key:
        sys.exit("Error: METABASE_URL, METABASE_QUESTION_ID, METABASE_API_KEY required")
    
    try:
        # Step 1: Export from Metabase
        print("[1/2] Exporting from Metabase...")
        client = MetabaseClient(url, api_key)
        output_file = f"data/metabase_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        row_count = client.export_to_csv(int(question_id), output_file)
        print(f"✓ Exported {row_count} rows to {output_file}\n")
        
        # Step 2: Send via email
        print("[2/2] Sending email...")
        send_csv_email(output_file)
        
        print(f"\n{'='*60}")
        print(f"✓ Monthly export completed successfully!")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n✗ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    run_monthly_export()
