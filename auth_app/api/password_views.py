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
                secure=not settings.DEBUG,
                samesite='None' if not settings.DEBUG else 'Lax',
                path="/",
                domain=getattr(settings, 'COOKIE_DOMAIN', None)
            )
            return response

        except TokenError:
            return Response({'detail': 'Ungültiger Refresh-Token.'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([AllowAny])
def password_reset_redirect(request, uidb64, token):
    """Redirect from email link to frontend password reset page (like colleague's implementation)."""
    
    frontend_url = build_frontend_url(f"pages/auth/confirm_password.html?uid={uidb64}&token={token}")
    
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


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_view(request):
    """POST /api/password_reset/ - Send password reset email."""
    serializer = PasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        try:
            user = CustomUser.objects.get(email=email)
            EmailService.send_password_reset_email(user)
        except CustomUser.DoesNotExist:
            pass
        
        return Response({
            'detail': 'An email has been sent to reset your password.'
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)