"""
Authentication Views
Handles user registration, login, and logout functionality.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

import logging

from ..models import CustomUser
from ..services.email_service import EmailService
from .serializers import UserRegistrationSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class RegistrationView(APIView):
    """API endpoint for registering a new user and sending a confirmation email with activation token."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Handle user registration, saves the account, generates an activation token, and triggers a confirmation email."""
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            saved_account = serializer.save()
            
            token = default_token_generator.make_token(saved_account)

            EmailService.send_registration_confirmation_email(saved_account, token)

            data = {
                'user': {
                    'id': saved_account.pk,
                    'email': saved_account.email
                },
                'token': token 
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Email or Password is invalid'
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Login endpoint that handles authentication and sets JWT cookies."""
    if request.method == 'POST':
        email = request.data.get('email')
        password = request.data.get('password')
        
        try:
            user = CustomUser.objects.get(email=email)
            if user.check_password(password) and user.is_active:
                refresh = RefreshToken.for_user(user)
                access = refresh.access_token
                
                response_data = {
                    "detail": "Login successful",
                    "user": {
                        "id": user.id,
                        "username": user.email
                    }
                }
                
                response = Response(response_data)
                response.set_cookie(
                    key="access_token",
                    value=str(access),
                    httponly=True,
                    secure=True,  
                    samesite="None",
                    path="/",
                    domain=getattr(settings, 'COOKIE_DOMAIN', None)
                )
                response.set_cookie(
                    key="refresh_token",
                    value=str(refresh),
                    httponly=True,
                    secure=True,   
                    samesite="None",
                    path="/",
                    domain=getattr(settings, 'COOKIE_DOMAIN', None)
                )
                return response
            else:
                return Response(
                    {"detail": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    """API endpoint for logging out and invalidating the user's refresh token."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Invalidate the refresh token and clear authentication cookies."""
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response({'detail': 'Refresh-Token fehlt.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass 

        response = Response({'detail': 'Logout successful! All tokens will be deleted. Refresh token is now invalid.'})
        response.delete_cookie('access_token', path="/", domain=getattr(settings, 'COOKIE_DOMAIN', None))
        response.delete_cookie('refresh_token', path="/", domain=getattr(settings, 'COOKIE_DOMAIN', None))
        return response


def blacklist_refresh_token(refresh_token: str) -> None:
    """Blacklist refresh token safely."""
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError:
        pass


def create_logout_response() -> Response:
    """Create logout success response."""
    return Response({
        'detail': 'Logout successful! All tokens will be deleted. Refresh token is now invalid.'
    }, status=status.HTTP_200_OK)


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies from response."""
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')


def get_refresh_token_from_request(request):
    """Get refresh token from request cookies."""
    return request.COOKIES.get('refresh_token')


def validate_logout_request(request):
    """Validate logout request and return token or error response."""
    refresh_token = get_refresh_token_from_request(request)
    if not refresh_token:
        return None, Response(
            {'detail': 'Refresh token missing.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    return refresh_token, None


def process_logout(refresh_token):
    """Process logout by blacklisting token and creating response."""
    blacklist_refresh_token(refresh_token)
    response = create_logout_response()
    clear_auth_cookies(response)
    return response