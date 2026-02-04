import uuid
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.conf import settings
from .validators import validate_future_date, validate_positive_decimal
from .managers import ShipmentManager


class Shipment(models.Model):
    """
    Platform listing created by users (cargo owners).
    Platforms can submit bids on active shipments via API.
    """
    STATUS_CHOICES = [
        ('active', _('აქტიური')),
        ('completed', _('დასრულებული')),
        ('cancelled', _('გაუქმებული')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shipments',
        verbose_name=_('განმცხადებელი')
    )
    pickup_location = models.TextField(
        _('ტვირთის აღების ადგილი'),
        help_text=_('ქალაქი, მისამართი')
    )
    pickup_date = models.DateTimeField(
        _('ტვირთის აღების თარიღი და დრო'),
        validators=[validate_future_date]
    )
    delivery_location = models.TextField(
        _('ტვირთის ჩაბარების ადგილი'),
        help_text=_('ქალაქი, მისამართი')
    )
    cargo_type = models.ForeignKey(
        'metadata.CargoType',
        on_delete=models.PROTECT,
        related_name='shipments_cargo',
        verbose_name=_('ტვირთის ტიპი')
    )
    cargo_volume = models.DecimalField(
        _('ტვირთის მოცულობა'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    volume_unit = models.ForeignKey(
        'metadata.VolumeUnit',
        on_delete=models.PROTECT,
        related_name='shipments_volume',
        verbose_name=_('მოცულობის ერთეული')
    )
    transport_type = models.ForeignKey(
        'metadata.TransportType',
        on_delete=models.PROTECT,
        related_name='shipments_transport',
        verbose_name=_('ტრანსპორტის ტიპი')
    )
    preferred_currency = models.ForeignKey(
        'metadata.Currency',
        on_delete=models.PROTECT,
        related_name='shipments_currency',
        verbose_name=_('სასურველი ვალუტა'),
        help_text=_('რომელ ვალუტაში მიიღებთ შეთავაზებებს')
    )
    additional_conditions = models.TextField(
        _('დამატებითი პირობები'),
        blank=True,
        null=True,
        max_length=500,
        help_text=_('დამატებითი მოთხოვნები ან შენიშვნები')
    )
    status = models.CharField(
        _('სტატუსი'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    selected_bid = models.ForeignKey(
        'bids.Bid',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='selected_for_shipment',
        verbose_name=_('არჩეული ბიდი')
    )
    created_at = models.DateTimeField(
        _('შექმნის თარიღი'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('განახლების თარიღი'),
        auto_now=True
    )
    completed_at = models.DateTimeField(
        _('დასრულების თარიღი'),
        null=True,
        blank=True
    )
    cancelled_at = models.DateTimeField(
        _('გაუქმების თარიღი'),
        null=True,
        blank=True
    )
    
    objects = ShipmentManager()
    
    class Meta:
        verbose_name = _('განაცხადი')
        verbose_name_plural = _('განაცხადები')
        db_table = 'shipments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.pickup_location} → {self.delivery_location}"
    
    @property
    def bids_count(self):
        """Return count of bids for this shipment."""
        return self.bids.count()
    
    @property
    def pending_bids_count(self):
        """Return count of pending bids."""
        return self.bids.filter(status='pending').count()
    
    @property
    def is_active_status(self):
        """Check if shipment is in active status."""
        return self.status == 'active'
    
    def clean(self):
        """Validate model fields."""
        super().clean()
        validate_future_date(self.pickup_date)
        validate_positive_decimal(self.cargo_volume)
    
    @transaction.atomic
    def mark_completed(self, bid):
        """
        Mark shipment as completed with a selected bid.
        1. Set status to 'completed'
        2. Set selected_bid
        3. Accept the selected bid
        4. Reject all other pending bids
        5. Create RejectedBidCache entries
        """
        from apps.bids.models import Bid
        
        # Validate bid belongs to this shipment
        if bid.shipment_id != self.id:
            raise ValueError(_('ბიდი არ ეკუთვნის ამ განაცხადს'))
        
        # Validate bid is pending
        if bid.status != 'pending':
            raise ValueError(_('მხოლოდ მოლოდინში მყოფი ბიდის მიღებაა შესაძლებელი'))
        
        # Mark shipment as completed
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.selected_bid = bid
        self.save(update_fields=['status', 'completed_at', 'selected_bid', 'updated_at'])
        
        # Accept the selected bid
        bid.accept()
        
        # Reject all other pending bids
        pending_bids = self.bids.filter(status='pending').exclude(id=bid.id)
        for pending_bid in pending_bids:
            pending_bid.reject()
    
    @transaction.atomic
    def mark_cancelled(self):
        """
        Mark shipment as cancelled.
        1. Set status to 'cancelled'
        2. Reject all pending bids
        3. Create RejectedBidCache entries
        """
        if self.status != 'active':
            raise ValueError(_('მხოლოდ აქტიური განაცხადის გაუქმებაა შესაძლებელი'))
        
        # Mark shipment as cancelled
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save(update_fields=['status', 'cancelled_at', 'updated_at'])
        
        # Reject all pending bids
        pending_bids = self.bids.filter(status='pending')
        for pending_bid in pending_bids:
            pending_bid.reject()
    
    @transaction.atomic
    def reject_all_pending_bids(self):
        """
        Reject all pending bids without changing shipment status.
        Useful when user wants to clear current bids but keep shipment active.
        """
        pending_bids = self.bids.filter(status='pending')
        for pending_bid in pending_bids:
            pending_bid.reject()
