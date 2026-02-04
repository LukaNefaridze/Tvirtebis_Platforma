from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import User

@receiver(post_save, sender=User)
def assign_default_group(sender, instance, created, **kwargs):
    """
    Automatically assign 'Client' group to new users with 'client' role.
    """
    if created and instance.role == 'client':
        client_group = Group.objects.filter(name='Client').first()
        if client_group:
            instance.groups.add(client_group)
