from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    ROLE_CHOICES = (
        ('doctor', _('Doctor')),
        ('patient', _('Patient')),
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='patient',
        help_text=_('Designates whether this user is a doctor or patient.')
    )
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    # Google Calendar Credentials
    google_access_token = models.TextField(null=True, blank=True)
    google_refresh_token = models.TextField(null=True, blank=True)
    google_token_uri = models.CharField(max_length=500, null=True, blank=True)
    google_client_id = models.CharField(max_length=500, null=True, blank=True)
    google_client_secret = models.CharField(max_length=500, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'role']

    class Meta(AbstractUser.Meta):
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_doctor(self):
        return self.role == 'doctor'

    @property
    def is_patient(self):
        return self.role == 'patient'
