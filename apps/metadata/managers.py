from django.db import models


class ActiveMetadataManager(models.Manager):
    """Manager that returns only active metadata records by default."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True).order_by('sort_order', 'name')
