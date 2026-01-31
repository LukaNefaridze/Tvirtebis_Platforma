"""
Dynamic sidebar navigation helpers for Django Unfold.
Permission callbacks are used to show/hide menu items based on user type.
"""


def is_admin_user(request):
    """Check if the current user is an AdminUser."""
    from apps.accounts.models import AdminUser
    return (
        hasattr(request, 'user') 
        and request.user.is_authenticated 
        and isinstance(request.user, AdminUser)
    )


def is_regular_user(request):
    """Check if the current user is a regular User."""
    from apps.accounts.models import User
    return (
        hasattr(request, 'user') 
        and request.user.is_authenticated 
        and isinstance(request.user, User)
    )
