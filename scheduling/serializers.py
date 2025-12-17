from rest_framework import serializers
from django.utils import timezone
from .models import Availability, Appointment
from users.serializers import UserListSerializer

class AvailabilitySerializer(serializers.ModelSerializer):
    doctor_details = UserListSerializer(source='doctor', read_only=True)

    class Meta:
        model = Availability
        fields = ['id', 'doctor', 'doctor_details', 'start_time', 'end_time', 'is_booked']
        read_only_fields = ['doctor', 'is_booked']

    def validate(self, attrs):
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        doctor = self.context['request'].user

        # 1. Basic Time Validation
        if start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")

        if start_time < timezone.now():
            raise serializers.ValidationError("Availability cannot be created in the past.")

        overlapping_slots = Availability.objects.filter(
            doctor=doctor,
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        # Exclude self if updating
        if self.instance:
            overlapping_slots = overlapping_slots.exclude(pk=self.instance.pk)

        if overlapping_slots.exists():
            raise serializers.ValidationError("This time slot overlaps with an existing availability.")

        return attrs

    def create(self, validated_data):
        # Automatically assign the logged-in doctor
        validated_data['doctor'] = self.context['request'].user
        return super().create(validated_data)


class AppointmentSerializer(serializers.ModelSerializer):
    availability_details = AvailabilitySerializer(source='availability', read_only=True)
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'patient_name', 'availability', 'availability_details', 'created_at', 'google_event_id']
        read_only_fields = ['patient', 'created_at', 'google_event_id']

    def validate_availability(self, value):
        if value.is_booked:
            raise serializers.ValidationError("This slot is already booked.")
        if value.start_time < timezone.now():
            raise serializers.ValidationError("Cannot book a past slot.")
        return value
