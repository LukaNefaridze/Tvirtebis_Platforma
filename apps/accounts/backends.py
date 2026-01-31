from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import User, AdminUser


class AdminUserBackend(ModelBackend):
    """
    Authentication backend for AdminUser model.
    This is the default backend since AUTH_USER_MODEL is AdminUser.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Authenticate AdminUser by email."""
        if username is None:
            username = kwargs.get('email')
        
        if username is None or password is None:
            return None
        
        try:
            user = AdminUser.objects.get(email=username)
        except AdminUser.DoesNotExist:
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        """Get AdminUser by ID."""
        try:
            return AdminUser.objects.get(pk=user_id)
        except AdminUser.DoesNotExist:
            return None


class RegularUserBackend(ModelBackend):
    """
    Authentication backend for regular User model (cargo owners).
    This allows Users to log in to the Django admin panel.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Authenticate User by email."""
        if username is None:
            username = kwargs.get('email')
        
        if username is None or password is None:
            return None
        
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        """Get User by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
