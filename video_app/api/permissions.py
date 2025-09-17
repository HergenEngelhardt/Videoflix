from rest_framework.permissions import BasePermission


class IsAuthenticatedForVideo(BasePermission):
    """
    Custom permission to check if user is authenticated for video access.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to only allow admins to edit videos.
    """
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_staff)