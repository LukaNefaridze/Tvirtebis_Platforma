from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import User


class PasswordChangeMiddleware:
    """
    Middleware to enforce password change for users with temporary passwords.
    Redirects regular Users away from Django admin to the user portal.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if user is authenticated and is a User instance (not AdminUser)
        if request.user.is_authenticated and isinstance(request.user, User):
            # Check if password change is required
            if request.user.must_change_password:
                # Exempt these URLs from redirect
                exempt_urls = [
                    reverse('accounts:password_change'),
                    '/admin/logout/',
                    '/static/',
                    '/media/',
                ]
                
                # Check if current path is exempt
                is_exempt = any(request.path.startswith(url) for url in exempt_urls)
                
                if not is_exempt:
                    messages.warning(
                        request,
                        _('თქვენ იყენებთ დროებით პაროლს. გთხოვთ შექმნათ ახალი პაროლი.')
                    )
                    return redirect('accounts:password_change')
            
            # Regular Users should NOT access Django admin at all
            # Redirect them to the user portal
            if request.path.startswith('/admin/'):
                # Allow only login and logout
                allowed_admin_paths = [
                    '/admin/login/',
                    '/admin/logout/',
                ]
                
                if not any(request.path.startswith(path) for path in allowed_admin_paths):
                    # Redirect to user portal
                    return redirect('accounts:shipments')
        
        response = self.get_response(request)
        return response
