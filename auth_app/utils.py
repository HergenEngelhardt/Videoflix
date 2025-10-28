"""
Utility functions for authentication app.
"""

from django.conf import settings


def build_frontend_url(path):
    """
    Build complete frontend URL with automatic path detection.
    """
    frontend_url = getattr(settings, 'FRONTEND_URL', '').rstrip('/')
    prefix = getattr(settings, 'FRONTEND_PATH_PREFIX', '')
    prefix = prefix.strip('/') if prefix is not None else ''
    path = path.lstrip('/')

    if prefix:
        final_url = f"{frontend_url}/{prefix}/{path}"
    else:
        final_url = f"{frontend_url}/{path}"

    return final_url