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
    """Activate user account if token is valid - improved robustness."""
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
    
    logger.info("Token validation failed")
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
    logger.debug(f"Activation request received - uidb64: {uidb64}, token: {token}")
    
    user = decode_user_from_uidb64(uidb64)
    logger.debug(f"User found: {user}")
    
    if user is None:
        logger.debug("User not found or invalid uidb64")
        return create_activation_error_response()
    
    if user.is_active:
        logger.debug(f"User {user.email} is already active")
        return Response(
            {'message': 'Account is already activated.'},
            status=status.HTTP_200_OK
        )
    
    if activate_user_account(user, token):
        logger.debug(f"User {user.email} successfully activated")
        return create_activation_success_response()
    
    logger.debug(f"Token validation failed for user {user.email}")
    return create_activation_error_response()


@api_view(['GET'])
@permission_classes([AllowAny])
def activate_redirect(request, uidb64, token):
    """Redirect from email link to frontend activation page (like colleague's implementation)."""
    logger.debug(f"activate_redirect - uidb64: {uidb64}, token: {token}")
    
    frontend_url = build_frontend_url(f"pages/auth/activate.html?uid={uidb64}&token={token}")
    logger.debug(f"frontend_url: {frontend_url}")
    
    return redirect(frontend_url)