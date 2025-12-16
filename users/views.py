from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserListSerializer
)
from django.shortcuts import redirect
from django.conf import settings
from google_auth_oauthlib.flow import Flow
from .forms import CustomUserCreationForm
import logging

logger = logging.getLogger(__name__)
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # type: ignore - 'objects' is a dynamic attribute on Django models
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserProfileSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            if not isinstance(data, dict):
                return Response(
                    {'error': 'Internal validation error'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            user = data['user']
            
            login(request, user)
            # type: ignore - 'objects' is a dynamic attribute on Django models
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'user': UserProfileSerializer(user).data,
                'token': token.key
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    def post(self, request):
        try:
            if request.user.is_authenticated:
                request.user.auth_token.delete()
                logout(request)
                return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
            return Response({'error': 'User not logged in'}, status=status.HTTP_400_BAD_REQUEST)
        except (AttributeError, Exception):
            return Response({'error': 'No active session found'}, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DoctorListView(generics.ListAPIView):
    queryset = User.objects.filter(role='doctor')
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAuthenticated]

class GoogleCalendarInitView(APIView):
    """
    Initiates the OAuth2 flow to link a Google Calendar account.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        flow = Flow.from_client_secrets_file(
            settings.GOOGLE_CLIENT_SECRETS_FILE,
            scopes=settings.GOOGLE_API_SCOPES,
            redirect_uri=settings.REDIRECT_URI
        )
        
        # access_type='offline' is crucial to get a refresh_token
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent' # Forces consent screen to ensure refresh_token is returned
        )

        request.session['google_oauth_state'] = state
        return redirect(authorization_url)


class GoogleCalendarRedirectView(APIView):
    """
    Callback view handling the response from Google.
    Stores credentials in the User model.
    """
    permission_classes = [permissions.AllowAny] 

    def get(self, request):
        state = request.session.get('google_oauth_state')
        
        if not state:
            return Response({'error': 'Missing state parameter'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            flow = Flow.from_client_secrets_file(
                settings.GOOGLE_CLIENT_SECRETS_FILE,
                scopes=settings.GOOGLE_API_SCOPES,
                state=state,
                redirect_uri=settings.REDIRECT_URI
            )

            # Fetch the token using the authorization code in the URL
            flow.fetch_token(authorization_response=request.build_absolute_uri())
            credentials = flow.credentials

            # Get the currently logged-in user
            user = request.user
            
            if not user.is_authenticated:
                return Response({'error': 'User must be logged in to link calendar'}, status=status.HTTP_401_UNAUTHORIZED)

            token_uri = getattr(credentials, 'token_uri', None)
            if not token_uri:
                token_uri = getattr(credentials, 'token_url', 'https://oauth2.googleapis.com/token')

            # Persist credentials to the database
            user.google_access_token = credentials.token
            user.google_refresh_token = credentials.refresh_token
            user.google_token_uri = token_uri
            user.google_client_id = credentials.client_id
            user.google_client_secret = credentials.client_secret
            user.save()

            return Response({'message': 'Google Calendar linked successfully!'})

        except Exception as e:
            logger.error(f"OAuth2 Callback Error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully! You can now log in.')
        return response

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_doctor:
            context['doctor_dashboard'] = True
        elif self.request.user.is_patient:
            context['patient_dashboard'] = True
        return context
