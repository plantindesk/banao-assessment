from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.views.generic import CreateView 
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
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.conf import settings
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
    Initiates Google Calendar OAuth flow.
    Accepts authentication via:
    - Session (cookie-based, for browser redirects)
    - Token (header-based, for API calls)
    - Query parameter token (for redirect-based flows)
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.AllowAny]  # We'll handle auth manually

    def get(self, request):
        user = None
        
        # Try to get user from session or token auth first
        if request.user.is_authenticated:
            user = request.user
        else:
            # Try to authenticate via query parameter token
            token_key = request.GET.get('token')
            if token_key:
                try:
                    token = Token.objects.get(key=token_key)
                    user = token.user
                    # Log the user in to create a session for the callback
                    login(request, user)
                except Token.DoesNotExist:
                    pass
        
        if not user:
            # Redirect to frontend with error
            return redirect(f"{settings.FRONTEND_URL}/calendar/callback?error=Authentication%20required")

        try:
            flow = Flow.from_client_secrets_file(
                settings.GOOGLE_CLIENT_SECRETS_FILE,
                scopes=settings.GOOGLE_API_SCOPES,
                redirect_uri=settings.REDIRECT_URI
            )
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            # Store state and user ID in session
            request.session['google_oauth_state'] = state
            request.session['google_oauth_user_id'] = user.id
            
            return redirect(authorization_url)
            
        except Exception as e:
            logger.error(f"Google Calendar Init Error: {e}")
            return redirect(f"{settings.FRONTEND_URL}/calendar/callback?error={str(e)}")


class GoogleCalendarRedirectView(APIView):
    """
    Handles the OAuth callback from Google.
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = [SessionAuthentication]

    def get(self, request):
        state = request.session.get('google_oauth_state')
        user_id = request.session.get('google_oauth_user_id')
        
        # Check for error from Google
        error = request.GET.get('error')
        if error:
            logger.error(f"Google OAuth Error: {error}")
            return redirect(f"{settings.FRONTEND_URL}/calendar/callback?error={error}")
        
        if not state:
            return redirect(f"{settings.FRONTEND_URL}/calendar/callback?error=Missing%20OAuth%20state")
        
        if not user_id:
            return redirect(f"{settings.FRONTEND_URL}/calendar/callback?error=Session%20expired")

        try:
            # Get user from stored user_id
            user = User.objects.get(id=user_id)
            
            flow = Flow.from_client_secrets_file(
                settings.GOOGLE_CLIENT_SECRETS_FILE,
                scopes=settings.GOOGLE_API_SCOPES,
                state=state,
                redirect_uri=settings.REDIRECT_URI
            )
            
            # Fetch the token
            flow.fetch_token(authorization_response=request.build_absolute_uri())
            credentials = flow.credentials

            # Get token_uri safely
            token_uri = getattr(credentials, 'token_uri', None)
            if not token_uri:
                token_uri = getattr(credentials, '_token_uri', 'https://oauth2.googleapis.com/token')

            # Save credentials to user
            user.google_access_token = credentials.token
            user.google_refresh_token = credentials.refresh_token
            user.google_token_uri = token_uri
            user.google_client_id = credentials.client_id
            user.google_client_secret = credentials.client_secret
            user.save()

            # Clean up session
            if 'google_oauth_state' in request.session:
                del request.session['google_oauth_state']
            if 'google_oauth_user_id' in request.session:
                del request.session['google_oauth_user_id']

            logger.info(f"Google Calendar connected for user: {user.email}")
            return redirect(f"{settings.FRONTEND_URL}/calendar/callback?success=true")

        except User.DoesNotExist:
            logger.error(f"User not found: {user_id}")
            return redirect(f"{settings.FRONTEND_URL}/calendar/callback?error=User%20not%20found")
        except Exception as e:
            logger.error(f"OAuth2 Callback Error: {e}")
            return redirect(f"{settings.FRONTEND_URL}/calendar/callback?error={str(e)}")


# Add endpoint to disconnect Google Calendar
class GoogleCalendarDisconnectView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        user.google_access_token = None
        user.google_refresh_token = None
        user.google_token_uri = None
        user.google_client_id = None
        user.google_client_secret = None
        user.save()
        
        return Response({'message': 'Google Calendar disconnected successfully'})


# Add endpoint to check Google Calendar status
class GoogleCalendarStatusView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        is_connected = bool(user.google_refresh_token)
        
        return Response({
            'connected': is_connected,
            'email': user.email if is_connected else None
        })
class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully! You can now log in.')
        return response

