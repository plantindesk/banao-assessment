from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def send_welcome_email_on_signup(sender, instance, created, **kwargs):
    """
    Send a welcome email when a new user is created.
    Listens for the post_save signal on the User model.
    """
    if not created:
        return

    # Get the user's display name, fallback to username if full name is empty
    user_name = instance.get_full_name() or instance.username

    email_payload = {
        "action": "SIGNUP_WELCOME",
        "recipient": instance.email,
        "data": {
            "userName": user_name
        }
    }

    try:
        requests.post(
            'http://localhost:3003/email/send',
            json=email_payload,
            timeout=5
        )
        logger.info(f"Welcome email triggered for user: {instance.email}")
    except requests.RequestException as e:
        # Log the error but do not crash the signup process
        logger.error(f"Failed to send welcome email to {instance.email}: {e}")
