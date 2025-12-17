from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AvailabilityViewSet, AppointmentViewSet

app_name = 'scheduling'

router = DefaultRouter()
router.register(r'availability', AvailabilityViewSet, basename='availability')
router.register(r'appointments', AppointmentViewSet, basename='appointments')

urlpatterns = [
    path('', include(router.urls)),
]
