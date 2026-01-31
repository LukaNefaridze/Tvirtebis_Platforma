from rest_framework import permissions


class IsAuthenticatedBroker(permissions.BasePermission):
    """
    Permission class that checks if the authenticated user is a Broker.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is a Broker."""
        from apps.bids.models import Broker
        
        return (
            request.user and
            request.user.is_authenticated and
            isinstance(request.user, Broker)
        )
