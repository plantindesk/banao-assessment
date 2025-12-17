# users/urls.py

from django.urls import path
from . import views
app_name = 'users'

urlpatterns = [
    # API endpoints
    path('register/', views.RegisterView.as_view(), name='api-register'),
    path('login/', views.LoginView.as_view(), name='api-login'),
    path('logout/', views.LogoutView.as_view(), name='api-logout'),
    path('profile/', views.ProfileView.as_view(), name='api-profile'),
    path('doctors/', views.DoctorListView.as_view(), name='api-doctor-list'),
    
    # Google Calendar Integration
    path('google-calendar/init/', views.GoogleCalendarInitView.as_view(), name='google-calendar-init'),
    # This path matches REDIRECT_URI in settings.py: http://localhost:8000/oauth2callback
    path('oauth2callback', views.GoogleCalendarRedirectView.as_view(), name='google-calendar-redirect'),
]
