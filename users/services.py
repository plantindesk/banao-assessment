from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def create_calendar_event(user, event_details):
    """
    Creates a Google Calendar event for the specified user.
    
    Args:
        user (User): The user instance (Doctor or Patient)
        event_details (dict): A dictionary matching the Google Calendar API event resource structure.
    """
    
    # 1. Check if user has linked Google Calendar
    if not user.google_refresh_token:
        logger.warning(f"User {user.email} has not linked Google Calendar. Skipping event creation.")
        return None

    # 2. Reconstruct Credentials from DB
    # We use a default token_uri if the one in DB is missing.
    token_uri = user.google_token_uri or 'https://oauth2.googleapis.com/token'

    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri=token_uri,
        client_id=user.google_client_id,
        client_secret=user.google_client_secret,
        scopes=settings.GOOGLE_API_SCOPES
    )

    # 3. Handle Token Refresh if expired
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save the new access token back to the DB
                user.google_access_token = creds.token
                user.save(update_fields=['google_access_token'])
            except Exception as e:
                logger.error(f"Failed to refresh token for user {user.email}: {str(e)}")
                return None
        else:
            logger.error(f"Credentials invalid and no refresh token for {user.email}")
            return None

    # 4. Insert Event
    try:
        service = build('calendar', 'v3', credentials=creds)
        event = service.events().insert(calendarId='primary', body=event_details).execute()
        logger.info(f"Event created for {user.email}: {event.get('htmlLink')}")
        return event
    except Exception as e:
        logger.error(f"Google API Error for user {user.email}: {str(e)}")
        return None
