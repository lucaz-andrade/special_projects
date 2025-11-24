import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

recipients = 'customer_success@zamp.com'

def send_csv_email(csv_file):
    """Send CSV file via Gmail."""
    load_dotenv()
    
    # Get config
    sender = os.getenv('GMAIL_EMAIL')
    password = os.getenv('GMAIL_APP_PASSWORD')
    
    
    # Validate
    if not sender or not password or not recipients[0]:
        sys.exit("Error: GMAIL_EMAIL, GMAIL_APP_PASSWORD, EMAIL_RECIPIENTS required in .env")
    if not os.path.exists(csv_file):
        sys.exit(f"Error: File not found: {csv_file}")
    
    # Build email
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = "Enabled/Disabled Review"
     # Email body
    body = f"""
            Action items for this report:
            - Review the file attached before 1st of each month
            - For any you have disabled, please update all disabled account/states notes like: “Disabled by Carie for billing reasons”
            - Review and adjust enabled/disabled setting as appropriate. 

        Context: https://3.basecamp.com/5828705/buckets/38536987/documents/9185041434#__recording_9293636945

        This is an automated message. Please do not reply to this email.
        """
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach CSV
    with open(csv_file, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(csv_file)}')
        msg.attach(part)
    
    # Send
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        print(f"✓ Email sent to {', '.join(recipients)}")
    except Exception as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python mailman.py <data/metabase_export_20251119_144721.csv>")
    send_csv_email(sys.argv[1])