from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        """Allow read access to all, write access only to owners."""
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        return obj.user == request.user
