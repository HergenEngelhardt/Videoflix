from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.shortcuts import get_object_or_404

from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer,
    PasswordResetSerializer,
    PasswordConfirmSerializer
)
from ..models import CustomUser
from ..utils import send_activation_email, send_password_reset_email


def create_user_response(user):
    """Create response data for user registration.
    Generates JWT tokens and user info for API responses."""
    refresh = RefreshToken.for_user(user)
    return {
        'user': {'id': user.id, 'email': user.email},
        'token': str(refresh.access_token)
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """POST /api/register/ - Register a new user and send activation email.
    Creates inactive user account and queues verification email."""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        send_activation_email(user)
        return Response(create_user_response(user), status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def decode_user_from_uidb64(uidb64):
    """Decode user ID from base64 and get user object.
    Safely extracts and validates user from encoded activation tokens."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return get_object_or_404(CustomUser, pk=uid)
    except (TypeError, ValueError, OverflowError):
        return None


def activate_user_account(user, token):
    """Activate user account if token is valid."""
    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return True
    return False


def create_activation_error_response():
    """Create activation error response."""
    return Response(
        {'message': 'Activation failed.'}, 
        status=status.HTTP_400_BAD_REQUEST
    )


def create_activation_success_response():
    """Create activation success response."""
    return Response(
        {'message': 'Account successfully activated.'}, 
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def activate_view(request, uidb64, token):
    """GET /api/activate/<uidb64>/<token>/ - Activate user account."""
    user = decode_user_from_uidb64(uidb64)
    if not user:
        return create_activation_error_response()
    
    if activate_user_account(user, token):
        return create_activation_success_response()
    else:
        return create_activation_error_response()


def create_login_response(user):
    """Create login response with user data."""
    return Response({
        'detail': 'Login successful',
        'user': {'id': user.id, 'username': user.email}
    }, status=status.HTTP_200_OK)


def set_auth_cookies(response, access_token, refresh_token, request):
    """Set authentication cookies on response."""
    is_secure = not request.META.get('HTTP_HOST', '').startswith('localhost')
    
    response.set_cookie(
        'access_token', str(access_token), max_age=3600,
        httponly=True, secure=is_secure, samesite='Lax'
    )
    response.set_cookie(
        'refresh_token', str(refresh_token), max_age=604800,
        httponly=True, secure=is_secure, samesite='Lax'
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """POST /api/login/ - Authenticate user and set HTTP-only cookies."""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        response = create_login_response(user)
        set_auth_cookies(response, refresh.access_token, refresh, request)
        return response
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


@api_view(['POST'])
def logout_view(request):
    """POST /api/logout/ - Logout user and blacklist refresh token."""
    refresh_token = request.COOKIES.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {'detail': 'Refresh token missing.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    blacklist_refresh_token(refresh_token)
    response = create_logout_response()
    clear_auth_cookies(response)
    
    return response


def create_refresh_response(access_token):
    """Create response for token refresh."""
    return Response({
        'detail': 'Token refreshed',
        'access': str(access_token)
    }, status=status.HTTP_200_OK)


def set_access_token_cookie(response, access_token, request):
    """Set access token cookie on response."""
    response.set_cookie(
        'access_token',
        str(access_token),
        max_age=3600, 
        httponly=True,
        secure=not request.META.get('HTTP_HOST', '').startswith('localhost'),
        samesite='Lax'
    )


@api_view(['POST'])
def token_refresh_view(request):
    """
    POST /api/token/refresh/
    Refresh access token using refresh token from cookie.
    """
    refresh_token = request.COOKIES.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {'detail': 'Refresh token missing.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = refresh.access_token
        
        response = create_refresh_response(access_token)
        set_access_token_cookie(response, access_token, request)
        return response
        
    except TokenError:
        return Response(
            {'detail': 'Invalid refresh token.'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


def send_reset_email_if_user_exists(email: str) -> None:
    """Send password reset email if user exists (security by obscurity)."""
    try:
        user = CustomUser.objects.get(email=email)
        send_password_reset_email(user)
    except CustomUser.DoesNotExist:
        pass


def create_password_reset_response() -> Response:
    """Create password reset response."""
    return Response({
        'detail': 'An email has been sent to reset your password.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_view(request):
    """POST /api/password_reset/ - Send password reset email."""
    serializer = PasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        send_reset_email_if_user_exists(email)
        return create_password_reset_response()
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def validate_reset_token(user, token):
    """Validate password reset token."""
    return default_token_generator.check_token(user, token)


def reset_user_password(user, new_password):
    """Reset user password."""
    user.set_password(new_password)
    user.save()


def validate_reset_request(uidb64: str, token: str) -> tuple:
    """Validate password reset request parameters."""
    user = decode_user_from_uidb64(uidb64)
    if not user:
        return None, Response(
            {'detail': 'Invalid reset link.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not validate_reset_token(user, token):
        return None, Response(
            {'detail': 'Invalid or expired token.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return user, None


def process_password_reset(request, user) -> Response:
    """Process password reset with new password."""
    serializer = PasswordConfirmSerializer(data=request.data)
    if serializer.is_valid():
        reset_user_password(user, serializer.validated_data['new_password'])
        return Response({
            'detail': 'Your Password has been successfully reset.'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_confirm_view(request, uidb64, token):
    """POST /api/password_confirm/<uidb64>/<token>/ - Confirm password reset."""
    user, error_response = validate_reset_request(uidb64, token)
    if error_response:
        return error_response
    
    return process_password_reset(request, user)