import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# --- Configuration ---
DEV_MODE = os.environ.get('DEV_MODE', 'True').lower() == 'true'
EMAIL_SERVICE_PROVIDER = os.environ.get('EMAIL_SERVICE_PROVIDER', 'CONSOLE')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@hospital-dev.com')
AWS_SES_REGION = os.environ.get('AWS_SES_REGION', 'us-east-1')
SMTP_HOST = os.environ.get('SMTP_HOST', 'localhost')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '1025'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')


# --- Email Templates ---
def get_signup_welcome_template(data: dict) -> tuple[str, str]:
    """Generates the HTML for the welcome email."""
    user_name = data.get('userName', 'User')
    subject = "Welcome to Our Service!"
    html_body = f"""
    <html>
    <body>
        <h1>Welcome, {user_name}!</h1>
        <p>Thank you for signing up for our amazing service. We're excited to have you on board.</p>
        <p>If you have any questions, feel free to reply to this email.</p>
        <br>
        <p>Best Regards,</p>
        <p>The Team</p>
    </body>
    </html>
    """
    return subject, html_body


def get_booking_confirmation_template(data: dict) -> tuple[str, str]:
    """Generates the HTML for the booking confirmation email."""
    user_name = data.get('userName', 'User')
    booking_id = data.get('bookingId', 'N/A')
    booking_details = data.get('details', 'No details provided.')
    subject = f"Booking Confirmation #{booking_id}"
    html_body = f"""
    <html>
    <body>
        <h1>Booking Confirmed, {user_name}!</h1>
        <p>Your booking with ID <strong>{booking_id}</strong> has been successfully confirmed.</p>
        <h3>Booking Details:</h3>
        <p>{booking_details}</p>
        <br>
        <p>We look forward to seeing you!</p>
        <p>Best Regards,</p>
        <p>The Team</p>
    </body>
    </html>
    """
    return subject, html_body


# --- Email Sending Logic ---
def send_via_console(recipient: str, subject: str, html_body: str) -> bool:
    """Prints email to console for development/testing."""
    print("\n" + "=" * 60)
    print("[EMAIL SENT] (Console Output)")
    print("=" * 60)
    print(f"TO:      {recipient}")
    print(f"FROM:    {SENDER_EMAIL}")
    print(f"SUBJECT: {subject}")
    print("-" * 60)
    print("BODY:")
    print(html_body)
    print("=" * 60 + "\n")
    return True


def send_via_ses(recipient: str, subject: str, html_body: str) -> bool:
    """Sends an email using AWS SES."""
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
    except ImportError:
        print("boto3 not installed. Falling back to console.")
        return send_via_console(recipient, subject, html_body)

    if not SENDER_EMAIL:
        print("SENDER_EMAIL not configured. Falling back to console.")
        return send_via_console(recipient, subject, html_body)

    try:
        ses_client = boto3.client('ses', region_name=AWS_SES_REGION)
        response = ses_client.send_email(
            Destination={'ToAddresses': [recipient]},
            Message={
                'Body': {'Html': {'Charset': 'UTF-8', 'Data': html_body}},
                'Subject': {'Charset': 'UTF-8', 'Data': subject},
            },
            Source=SENDER_EMAIL,
        )
        print(f"SES email sent! Message ID: {response['MessageId']}")
        return True
    except Exception as e:
        print(f"SES error: {e}. Falling back to console.")
        return send_via_console(recipient, subject, html_body)


def send_via_smtp(recipient: str, subject: str, html_body: str) -> bool:
    """Sends an email using SMTP server."""
    if not SENDER_EMAIL:
        print("SENDER_EMAIL not configured. Falling back to console.")
        return send_via_console(recipient, subject, html_body)

    requires_auth = bool(SMTP_USER and SMTP_PASSWORD)

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            if requires_auth:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
        print(f"SMTP email sent to {recipient}!")
        return True
    except Exception as e:
        print(f"SMTP error: {e}. Falling back to console.")
        return send_via_console(recipient, subject, html_body)


def send_email_internal(recipient: str, subject: str, html_body: str) -> bool:
    """Routes email to the appropriate provider."""
    provider = EMAIL_SERVICE_PROVIDER.upper()

    if DEV_MODE:
        return send_via_console(recipient, subject, html_body)

    if provider == 'SES':
        return send_via_ses(recipient, subject, html_body)
    elif provider == 'SMTP':
        return send_via_smtp(recipient, subject, html_body)
    else:
        return send_via_console(recipient, subject, html_body)


# --- Main Lambda Handler ---
def send_email(event: dict, context: object) -> dict:
    """Main handler to process the request and send the email."""
    try:
        body = json.loads(event.get('body', '{}'))
        action = body.get('action')
        recipient = body.get('recipient')
        data = body.get('data', {})

        if not action or not recipient:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Error: "action" and "recipient" are required.'})
            }

        if action == 'SIGNUP_WELCOME':
            subject, html_body = get_signup_welcome_template(data)
        elif action == 'BOOKING_CONFIRMATION':
            subject, html_body = get_booking_confirmation_template(data)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': f'Error: Unknown action "{action}"'})
            }

        success = send_email_internal(recipient, subject, html_body)

        if success:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': f'Email sent successfully to {recipient}!'})
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Failed to send email.'})
            }

    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Error: Invalid JSON in request body.'})
        }
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'An internal server error occurred.'})
        }
