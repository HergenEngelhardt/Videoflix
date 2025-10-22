"""
Password Reset and Token Views
Handles password reset functionality and JWT token refresh.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.conf import settings

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

import logging

from ..models import CustomUser
from ..utils import build_frontend_url
from ..services.email_service import EmailService
from .serializers import PasswordResetSerializer, PasswordResetConfirmSerializer

User = get_user_model()
logger = logging.getLogger(__name__)


class CookieRefreshView(TokenRefreshView):
    """API endpoint to refresh access tokens using a refresh token stored in cookies."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Validate the refresh token from cookies, issues a new access token, and sets it in a secure cookie."""
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'detail': 'Refresh token not found in cookies.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = refresh.access_token

            response = Response({
                'detail': 'Token refreshed',
                'access': str(access_token)  
            })
            response.set_cookie(
                key="access_token",
                value=str(access_token),
                httponly=True,
                secure=True,
                samesite="None",
                path="/",
                domain=getattr(settings, 'COOKIE_DOMAIN', None)
            )
            return response

        except TokenError:
            return Response({'detail': 'Ungültiger Refresh-Token.'}, status=status.HTTP_401_UNAUTHORIZED)


def get_cookie_security_setting(request):
    """Determine if cookies should use secure flag."""
    from django.conf import settings
    if settings.DEBUG:
        return False
    return not request.META.get('HTTP_HOST', '').startswith('localhost')


def send_password_reset_to_user(email):
    """Send password reset email to user if they exist."""
    try:
        user = CustomUser.objects.get(email=email, is_active=True)
        EmailService.send_password_reset_email(user)
    except CustomUser.DoesNotExist:
        pass


@api_view(['GET'])
@permission_classes([AllowAny])
def password_reset_redirect(request, uidb64, token):
    """Redirect from email link to frontend password reset page (like colleague's implementation)."""
    logger.debug(f"password_reset_redirect - uidb64: {uidb64}, token: {token}")
    
    frontend_url = build_frontend_url(f"pages/auth/confirm_password.html?uid={uidb64}&token={token}")
    logger.debug(f"frontend_url: {frontend_url}")
    
    return redirect(frontend_url)


class PasswordResetConfirmView(APIView):
    """API endpoint for password reset confirmation."""
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        """Redirect to frontend password reset page where initPasswordReset() will handle validation."""
        frontend_url = build_frontend_url(f"pages/auth/confirm_password.html?uid={uidb64}&token={token}")
        return redirect(frontend_url)

    def post(self, request, uidb64, token):
        """Verify the reset token and set the new password."""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(CustomUser, pk=uid)

            if not default_token_generator.check_token(user, token):
                raise Http404("Invalid or expired reset link.")

            serializer = PasswordResetConfirmSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user)
                return Response({
                    'detail': 'Your Password has been successfully reset.'
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response({
                'detail': 'Invalid or expired reset link.'
            }, status=status.HTTP_400_BAD_REQUEST)


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


def validate_refresh_token_from_cookies(request):
    """Validate and return refresh token from cookies."""
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        return None, Response(
            {'detail': 'Refresh token missing.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    return refresh_token, None


def create_invalid_refresh_token_response():
    """Create invalid refresh token response."""
    return Response(
        {'detail': 'Invalid refresh token.'},
        status=status.HTTP_401_UNAUTHORIZED
    )


def process_token_refresh(refresh_token, request):
    """Process token refresh and return response."""
    try:
        refresh = RefreshToken(refresh_token)
        access_token = refresh.access_token

        response = create_refresh_response(access_token)
        set_access_token_cookie(response, access_token, request)
        return response

    except TokenError:
        return create_invalid_refresh_token_response()


@api_view(['POST'])
@permission_classes([AllowAny])
def token_refresh_view(request):
    """
    POST /api/token/refresh/
    Refresh access token using refresh token from cookie.
    """
    refresh_token, error_response = validate_refresh_token_from_cookies(request)
    if error_response:
        return error_response

    return process_token_refresh(refresh_token, request)


def send_reset_email_if_user_exists(email: str) -> None:
    """Send password reset email if user exists (security by obscurity)."""
    try:
        user = CustomUser.objects.get(email=email)
        EmailService.send_password_reset_email(user)
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


def create_invalid_reset_link_response():
    """Create invalid reset link response."""
    return Response(
        {'detail': 'Invalid reset link.'},
        status=status.HTTP_400_BAD_REQUEST
    )


def create_invalid_token_response():
    """Create invalid token response."""
    return Response(
        {'detail': 'Invalid or expired token.'},
        status=status.HTTP_400_BAD_REQUEST
    )


def validate_reset_request(uidb64: str, token: str) -> tuple:
    """Validate password reset request parameters."""
    from .activation_views import decode_user_from_uidb64
    user = decode_user_from_uidb64(uidb64)
    if not user:
        return None, create_invalid_reset_link_response()

    if not validate_reset_token(user, token):
        return None, create_invalid_token_response()

    return user, None


def create_password_reset_success_response():
    """Create password reset success response."""
    return Response({
        'detail': 'Your Password has been successfully reset.'
    }, status=status.HTTP_200_OK)


def process_password_reset(request, user) -> Response:
    """Process password reset with new password."""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        reset_user_password(user, serializer.validated_data['new_password'])
        return create_password_reset_success_response()

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_confirm_view(request, uidb64, token):
    """POST /api/password_confirm/<uidb64>/<token>/ - Confirm password reset."""
    user, error_response = validate_reset_request(uidb64, token)
    if error_response:
        return error_response

    return process_password_reset(request, user)