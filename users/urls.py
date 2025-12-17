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
    
# Google Calendar endpoints
    path('google-calendar/init/', views.GoogleCalendarInitView.as_view(), name='google-calendar-init'),
    path('google-calendar/status/', views.GoogleCalendarStatusView.as_view(), name='google-calendar-status'),
    path('google-calendar/disconnect/', views.GoogleCalendarDisconnectView.as_view(), name='google-calendar-disconnect'),
    path('oauth2callback', views.GoogleCalendarRedirectView.as_view(), name='google-calendar-redirect'),
]
