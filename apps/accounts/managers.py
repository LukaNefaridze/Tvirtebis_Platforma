from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class AdminUserManager(BaseUserManager):
    """Manager for AdminUser model."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular admin user."""
        if not email:
            raise ValueError(_('ელ. ფოსტა სავალდებულოა'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class UserManager(BaseUserManager):
    """Manager for regular User model."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError(_('ელ. ფოსტა სავალდებულოა'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def active(self):
        """Return only active users."""
        return self.filter(is_active=True)
