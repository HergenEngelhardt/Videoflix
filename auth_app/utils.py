"""
Utility functions for authentication app.
"""

from django.conf import settings


def build_frontend_url(path):
    """Build complete frontend URL with automatic path detection.

    Args:
        path (str): Relative path from frontend root (e.g., 'pages/auth/activate.html')

    Returns:
        str: Complete frontend URL
    """
    frontend_url = settings.FRONTEND_URL.rstrip('/')
    path = path.lstrip('/')

    final_url = f"{frontend_url}/frontend/{path}"

    return final_url