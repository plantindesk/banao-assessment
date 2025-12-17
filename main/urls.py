from users.views import GoogleCalendarRedirectView
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('oauth2callback', GoogleCalendarRedirectView.as_view(), name='google-calendar-redirect'),
]
