import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv


def send_csv_email(csv_file):
    """Send CSV file via Gmail."""
    load_dotenv()
    
    # Get config
    sender = os.getenv('GMAIL_EMAIL')
    password = os.getenv('GMAIL_APP_PASSWORD')
    recipients = os.getenv('EMAIL_RECIPIENTS', '').split(',')
    
    # Validate
    if not sender or not password or not recipients[0]:
        sys.exit("Error: GMAIL_EMAIL, GMAIL_APP_PASSWORD, EMAIL_RECIPIENTS required in .env")
    if not os.path.exists(csv_file):
        sys.exit(f"Error: File not found: {csv_file}")
    
    # Build email
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = "Test Email - Scheduling System"
     # Email body
    body = f"""This is a test. I'm building a scheduling system to run monthly exports and emails.

        File: {os.path.basename(csv_file)}
        Best regards,
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