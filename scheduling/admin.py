from django.contrib import admin
from .models import Availability, Appointment

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'start_time', 'end_time', 'is_booked')
    list_filter = ('is_booked', 'start_time', 'doctor__username')
    search_fields = ('doctor__username', 'doctor__email')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'get_doctor', 'get_start_time', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('patient__username', 'patient__email', 'availability__doctor__username')

    def get_doctor(self, obj):
        return obj.availability.doctor.username
    get_doctor.short_description = 'Doctor'

    def get_start_time(self, obj):
        return obj.availability.start_time
    get_start_time.short_description = 'Slot Time'
