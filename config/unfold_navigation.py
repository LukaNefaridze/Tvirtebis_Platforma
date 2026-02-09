"""
Dynamic sidebar navigation helpers for Django Unfold.
Permission callbacks are used to show/hide menu items based on user type.
"""


def is_admin_user(request):
    """Check if the current user is an AdminUser."""
    return (
        hasattr(request, 'user') 
        and request.user.is_authenticated 
        and (request.user.is_superuser or getattr(request.user, 'role', '') == 'admin')
    )


def is_regular_user(request):
    """Check if the current user is a regular User."""
    return (
        hasattr(request, 'user') 
        and request.user.is_authenticated 
        and getattr(request.user, 'role', '') == 'client'
    )
