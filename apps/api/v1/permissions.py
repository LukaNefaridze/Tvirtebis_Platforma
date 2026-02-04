from rest_framework import permissions


class IsAuthenticatedPlatform(permissions.BasePermission):
    """
    Permission class that checks if the authenticated user is a Platform.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is a Platform."""
        from apps.bids.models import Platform
        
        return (
            request.user and
            request.user.is_authenticated and
            isinstance(request.user, Platform)
        )
