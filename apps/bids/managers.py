from django.db import models
from django.utils.translation import gettext_lazy as _


class BidManager(models.Manager):
    """Custom manager for Bid model with business logic."""
    
    def can_submit_bid(self, shipment, broker, price, estimated_delivery_time, currency):
        """
        Check if a bid can be submitted.
        Returns (can_submit: bool, error_code: str, error_message: str)
        """
        # Check if shipment is active
        if shipment.status != 'active':
            return False, 'SHIPMENT_NOT_ACTIVE', _('განაცხადზე შეთავაზებების მიღება აღარ არის შესაძლებელი')
        
        # Check if currency matches shipment's preferred currency
        if currency.id != shipment.preferred_currency_id:
            return False, 'CURRENCY_MISMATCH', _('ვალუტა უნდა ემთხვეოდეს განაცხადის ვალუტას')
        
        # Check for exact duplicate of rejected bid
        from .models import RejectedBidCache
        duplicate_exists = RejectedBidCache.objects.filter(
            shipment=shipment,
            broker=broker,
            price=price,
            estimated_delivery_time=estimated_delivery_time,
            currency=currency
        ).exists()
        
        if duplicate_exists:
            return False, 'BID_DUPLICATE', _('იგივე პარამეტრებით შეთავაზება უკვე გაკეთებული და უარყოფილია')
        
        return True, None, None


class ActiveBrokerManager(models.Manager):
    """Manager that returns only active brokers."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
