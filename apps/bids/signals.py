import logging
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def send_webhook_async(url, payload):
    """Send webhook in a separate thread to avoid blocking."""
    import requests
    
    try:
        response = requests.post(
            url,
            json=payload,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code >= 400:
            logger.warning(
                f"Webhook returned {response.status_code} for {url}: {response.text[:200]}"
            )
        else:
            logger.info(f"Webhook sent successfully to {url}")
    except requests.exceptions.Timeout:
        logger.error(f"Webhook timeout for {url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Webhook failed for {url}: {e}")


@receiver(post_save, sender='bids.Bid')
def send_bid_status_webhook(sender, instance, created, **kwargs):
    """
    Send webhook notification when bid status changes to accepted or rejected.
    
    Only sends webhooks for status changes (not on creation).
    Runs asynchronously to avoid blocking the request.
    """
    # Skip if this is a new bid (status will be 'pending')
    if created:
        return
    
    # Only send webhooks for accepted/rejected status
    if instance.status not in ['accepted', 'rejected']:
        return
    
    # Check if broker has a webhook URL configured
    webhook_url = instance.broker.webhook_url
    if not webhook_url:
        logger.debug(
            f"No webhook URL configured for broker {instance.broker.company_name}"
        )
        return
    
    # Build payload with bid and shipment details
    payload = {
        'event': f'bid_{instance.status}',
        'bid': {
            'id': str(instance.id),
            'status': instance.status,
            'company_name': instance.company_name,
            'price': str(instance.price),
            'currency': instance.currency.code,
            'estimated_delivery_time': instance.estimated_delivery_time,
            'contact_person': instance.contact_person,
            'contact_phone': instance.contact_phone,
        },
        'shipment': {
            'id': str(instance.shipment.id),
            'pickup_location': instance.shipment.pickup_location,
            'delivery_location': instance.shipment.delivery_location,
            'pickup_date': instance.shipment.pickup_date.isoformat(),
            'status': instance.shipment.status,
        },
        'broker': {
            'id': str(instance.broker.id),
            'company_name': instance.broker.company_name,
        }
    }
    
    # Send webhook asynchronously
    thread = threading.Thread(
        target=send_webhook_async,
        args=(webhook_url, payload),
        daemon=True
    )
    thread.start()
    
    logger.info(
        f"Webhook queued for bid {instance.id} ({instance.status}) to {webhook_url}"
    )
