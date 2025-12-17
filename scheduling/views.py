from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.request import Request
from django.db import transaction, DatabaseError
from django.db.models import QuerySet
from django.utils import timezone
from typing import TYPE_CHECKING, Any, TypeGuard
import requests
import logging

from .models import Availability, Appointment
from .serializers import AvailabilitySerializer, AppointmentSerializer
from users.permissions import IsDoctor
from users.services import create_calendar_event

if TYPE_CHECKING:
    from users.models import User

logger = logging.getLogger(__name__)


def get_authenticated_user(request: Request) -> "User | None":
    user = request.user
    if user.is_authenticated:
        return user
    return None


def is_authenticated_user(user: Any) -> TypeGuard["User"]:
    return bool(getattr(user, 'is_authenticated', False))


class AvailabilityViewSet(viewsets.ModelViewSet):
    serializer_class = AvailabilitySerializer

    def get_permissions(self) -> list[permissions.BasePermission]:
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsDoctor()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self) -> QuerySet[Availability]:
        user = self.request.user
        if not is_authenticated_user(user):
            return Availability.objects.none()

        if user.is_doctor:
            return Availability.objects.filter(doctor=user)
        elif user.is_patient:
            return Availability.objects.filter(
                is_booked=False,
                start_time__gt=timezone.now()
            )
        return Availability.objects.none()


class AppointmentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Appointment]:
        user = self.request.user
        if not is_authenticated_user(user):
            return Appointment.objects.none()

        if user.is_doctor:
            return Appointment.objects.filter(availability__doctor=user)
        return Appointment.objects.filter(patient=user)

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = get_authenticated_user(request)

        # Verify authentication first
        if user is None:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verify patient role
        if not user.is_patient:
            return Response(
                {"detail": "Only patients can book appointments."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Safely extract availability_id from request data
        data = request.data if isinstance(request.data, dict) else {}
        availability_id: Any = data.get('availability')

        if not availability_id:
            return Response(
                {"availability": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                availability_slot = Availability.objects.select_for_update().get(
                    pk=availability_id
                )

                if availability_slot.is_booked:
                    return Response(
                        {"detail": "This slot has already been booked."},
                        status=status.HTTP_409_CONFLICT
                    )

                availability_slot.is_booked = True
                availability_slot.save()

                appointment = Appointment.objects.create(
                    patient=user,
                    availability=availability_slot
                )

        except Availability.DoesNotExist:
            return Response(
                {"detail": "Availability slot not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except DatabaseError:
            return Response(
                {"detail": "An error occurred while processing the booking."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        self._handle_integrations(appointment)

        serializer = self.get_serializer(appointment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _handle_integrations(self, appointment: Appointment) -> None:
        doctor = appointment.availability.doctor
        patient = appointment.patient
        start_time = appointment.availability.start_time
        end_time = appointment.availability.end_time

        # 1. Google Calendar: Doctor
        doctor_event_body = {
            'summary': f'Appointment with {patient.get_full_name()}',
            'description': f'Patient Email: {patient.email}',
            'start': {'dateTime': start_time.isoformat()},
            'end': {'dateTime': end_time.isoformat()},
        }
        create_calendar_event(doctor, doctor_event_body)

        # 2. Google Calendar: Patient
        patient_event_body = {
            'summary': f'Appointment with Dr. {doctor.get_full_name()}',
            'description': f'Doctor Email: {doctor.email}',
            'start': {'dateTime': start_time.isoformat()},
            'end': {'dateTime': end_time.isoformat()},
        }
        patient_event = create_calendar_event(patient, patient_event_body)

        # Save patient's event ID if created
        if patient_event:
            appointment.google_event_id = patient_event.get('id')
            appointment.save(update_fields=['google_event_id'])

        # 3. Send booking confirmation email via email service
        details = f"Appointment with Dr. {doctor.get_full_name()} on {start_time.strftime('%Y-%m-%d at %H:%M')}"
        
        email_payload = {
            "action": "BOOKING_CONFIRMATION",
            "recipient": patient.email,
            "data": {
                "userName": patient.get_full_name(),
                "bookingId": str(appointment.id),
                "details": details
            }
        }

        try:
            requests.post(
                'http://localhost:3003/email/send',
                json=email_payload,
                timeout=5
            )
        except requests.RequestException as e:
            # Log the error but do not crash or rollback the booking
            logger.error(f"Failed to send booking confirmation email: {e}")
