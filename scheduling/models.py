from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class Availability(models.Model):
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availabilities',
        limit_choices_to={'role': 'doctor'}
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Availability Slot')
        verbose_name_plural = _('Availability Slots')
        ordering = ['start_time']

    def clean(self) -> None:
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time.")

    def save(self, *args, **kwargs) -> None:
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.doctor.username} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"


class Appointment(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments',
        limit_choices_to={'role': 'patient'}
    )
    availability = models.OneToOneField(
        Availability,
        on_delete=models.CASCADE,
        related_name='appointment'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    google_event_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Appointment')
        verbose_name_plural = _('Appointments')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Appt: {self.patient.username} with {self.availability.doctor.username}"
