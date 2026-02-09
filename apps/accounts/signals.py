from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import User

@receiver(post_save, sender=User)
def assign_default_permissions(sender, instance, created, **kwargs):
    """
    Handle permission assignment on user creation:
    1. Assign 'Client' group to new users with 'client' role.
    2. Copy permissions from 'admin@test.com' to new users with 'admin' role.
    """
    if not created:
        return

    # Case 1: Client Role
    if instance.role == 'client':
        client_group = Group.objects.filter(name='Client').first()
        if client_group:
            instance.groups.add(client_group)

    # Case 2: Admin Role
    elif instance.role == 'admin':
        try:
            # Find the template admin user
            template_admin = User.objects.get(email='admin@test.com')
            
            # Copy status flags
            instance.is_staff = template_admin.is_staff
            instance.is_superuser = template_admin.is_superuser
            
            # Copy groups
            instance.groups.set(template_admin.groups.all())
            
            # Copy direct user permissions
            instance.user_permissions.set(template_admin.user_permissions.all())
            
            # Save the changes
            instance.save()
            
        except User.DoesNotExist:
            # Log error or handle case where template admin doesn't exist
            print("Warning: Template user 'admin@test.com' not found. Permissions were not copied.")
