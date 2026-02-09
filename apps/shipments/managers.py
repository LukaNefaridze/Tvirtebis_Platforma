from django.db import models
from django.utils import timezone


class ShipmentManager(models.Manager):
    """Custom manager for Shipment model."""
    
    def active(self):
        """Return only active shipments."""
        return self.filter(status='active')
    
    def completed(self):
        """Return only completed shipments."""
        return self.filter(status='completed')
    
    def cancelled(self):
        """Return only cancelled shipments."""
        return self.filter(status='cancelled')
    
    def upcoming(self):
        """Return active shipments with pickup date in the future."""
        return self.filter(
            status='active',
            pickup_date__gt=timezone.now()
        )
