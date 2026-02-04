from django.db import models
from django.utils.translation import gettext_lazy as _


class BidManager(models.Manager):
    """Custom manager for Bid model with business logic."""
    
    def can_submit_bid(self, shipment, platform, price, estimated_delivery_time, currency, company_name, external_user_id=None):
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
            platform=platform,
            price=price,
            estimated_delivery_time=estimated_delivery_time,
            currency=currency,
            external_user_id=external_user_id
        ).exists()
        
        if duplicate_exists:
            return False, 'BID_DUPLICATE', _('იგივე პარამეტრებით შეთავაზება უკვე გაკეთებული და უარყოფილია')

        # Check for exact duplicate in existing bids (pending, accepted, rejected)
        if self.filter(
            shipment=shipment,
            platform=platform,
            price=price,
            estimated_delivery_time=estimated_delivery_time,
            currency=currency,
            company_name=company_name,
            external_user_id=external_user_id
        ).exists():
            return False, 'BID_EXACT_DUPLICATE', _('ზუსტად ასეთი შეთავაზება უკვე არსებობს')

        # Check if the price is the same as the previous bid from the same company
        last_bid = self.filter(
            shipment=shipment,
            platform=platform,
            company_name=company_name,
            external_user_id=external_user_id
        ).order_by('-created_at').first()

        if last_bid and last_bid.price == price:
            return False, 'BID_PRICE_DUPLICATE', _('ფასი უნდა განსხვავდებოდეს წინა შეთავაზებისგან')
        
        return True, None, None


class ActivePlatformManager(models.Manager):
    """Manager that returns only active platforms."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
