"""
Account Activation Views
Handles user account activation functionality.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

import logging

from ..models import CustomUser
from ..utils import build_frontend_url

User = get_user_model()
logger = logging.getLogger(__name__)


def decode_user_from_uidb64(uidb64):
    """Decode user ID from base64 and get user object."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        return None


def activate_user_account(user, token):
    """Activate user account if token is valid - simple and robust solution."""
    logger.info(f"Checking activation token for user id={user.pk} email={user.email}")
    
    if user.is_active:
        logger.info(f"User {user.email} is already active")
        return True
    
    if default_token_generator.check_token(user, token):
        logger.info("Token is valid, activating user")
        user.is_active = True
        user.save()
        logger.info(f"User {user.email} activated successfully")
        return True
    
    logger.warning(f"Token validation failed for user {user.email}")
    return False
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
def activate_account(request, uidb64, token):
    """Activate user account using token from email - returns JSON response."""
    
    user = decode_user_from_uidb64(uidb64)
    
    if user is None:
        logger.warning(f"Invalid uidb64 provided: {uidb64}")
        return create_activation_error_response()
    
    if user.is_active:
        logger.info(f"User {user.email} is already active - returning success")
        return Response(
            {'message': 'Account successfully activated.'},
            status=status.HTTP_200_OK
        )
    
    if activate_user_account(user, token):
        logger.info(f"User {user.email} successfully activated via token")
        return create_activation_success_response()
    
    logger.error(f"Activation failed for user {user.email}")
    return create_activation_error_response()


@api_view(['GET'])
@permission_classes([AllowAny])
def activate_redirect(request, uidb64, token):
    """Redirect from email link to frontend activation page (like colleague's implementation)."""
    
    frontend_url = build_frontend_url(f"pages/auth/activate.html?uid={uidb64}&token={token}")
    logger.info(f"Redirecting to: {frontend_url}")
    
    return redirect(frontend_url)