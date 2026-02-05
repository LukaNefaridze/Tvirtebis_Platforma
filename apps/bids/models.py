import uuid
import secrets
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.conf import settings
from .managers import BidManager, ActivePlatformManager


class Platform(models.Model):
    """
    Platform model - external companies that submit bids on shipments.
    Platforms access the platform via REST API with individual API keys.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    company_name = models.CharField(
        _('კომპანიის დასახელება'),
        max_length=200
    )
    contact_email = models.EmailField(
        _('საკონტაქტო ელ. ფოსტა')
    )
    contact_phone = models.CharField(
        _('საკონტაქტო ტელეფონი'),
        max_length=20
    )
    contact_person = models.CharField(
        _('საკონტაქტო პირი'),
        max_length=100,
        blank=True,
        null=True
    )
    is_active = models.BooleanField(
        _('აქტიური'),
        default=True
    )
    created_at = models.DateTimeField(
        _('შექმნის თარიღი'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('განახლების თარიღი'),
        auto_now=True
    )
    
    # Soft delete fields
    is_deleted = models.BooleanField(
        _('წაშლილია'),
        default=False
    )
    deleted_at = models.DateTimeField(
        _('წაშლის თარიღი'),
        null=True,
        blank=True
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_platforms',
        verbose_name=_('წაშალა')
    )
    
    objects = models.Manager()
    active = ActivePlatformManager()
    
    class Meta:
        verbose_name = _('პლათფორმა')
        verbose_name_plural = _('პლათფორმები')
        db_table = 'platforms'
    
    def __str__(self):
        return self.company_name

    @property
    def is_authenticated(self):
        """Always return True for active brokers."""
        return self.is_active


class PlatformAPIKey(models.Model):
    """
    API Key for broker authentication.
    Keys are hashed before storage (like passwords).
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    platform = models.ForeignKey(
        Platform,
        on_delete=models.CASCADE,
        related_name='api_keys',
        verbose_name=_('პლათფორმა')
    )
    api_key_hash = models.CharField(
        _('API გასაღების ჰეში'),
        max_length=128,
        unique=True,
        db_index=True
    )
    key = models.CharField(
        _('API გასაღები'),
        max_length=128,
        blank=True,
        null=True,
        help_text=_('შენახულია ღია ტექსტად ადმინ პანელში ჩვენებისთვის')
    )
    is_active = models.BooleanField(
        _('აქტიური'),
        default=True
    )
    created_at = models.DateTimeField(
        _('შექმნის თარიღი'),
        auto_now_add=True
    )
    last_used_at = models.DateTimeField(
        _('ბოლო გამოყენების თარიღი'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('API გასაღები')
        verbose_name_plural = _('API გასაღებები')
        db_table = 'platform_api_keys'
    
    def __str__(self):
        return f"API Key for {self.platform.company_name}"
    
    @staticmethod
    def generate_key():
        """Generate a random API key (32 bytes = 64 hex chars)."""
        return secrets.token_urlsafe(32)
    
    def set_key(self, raw_key):
        """Hash and store the API key."""
        self.key = raw_key
        self.api_key_hash = make_password(raw_key)
    
    def check_key(self, raw_key):
        """Verify an API key against the stored hash."""
        return check_password(raw_key, self.api_key_hash)
    
    def mark_used(self):
        """Update last_used_at timestamp."""
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])


class Bid(models.Model):
    """
    Bid submitted by a broker on a shipment.
    """
    STATUS_CHOICES = [
        ('pending', _('მოლოდინში')),
        ('accepted', _('მიღებული')),
        ('rejected', _('უარყოფილი')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    shipment = models.ForeignKey(
        'shipments.Shipment',
        on_delete=models.CASCADE,
        related_name='bids',
        verbose_name=_('განაცხადი')
    )
    platform = models.ForeignKey(
        Platform,
        on_delete=models.CASCADE,
        related_name='bids',
        verbose_name=_('პლათფორმა')
    )
    company_name = models.CharField(
        _('კომპანიის დასახელება'),
        max_length=200,
        help_text=_('პლათფორმის მიერ წარმოდგენილი კომპანია')
    )
    price = models.DecimalField(
        _('ფასი'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    currency = models.ForeignKey(
        'metadata.Currency',
        on_delete=models.PROTECT,
        related_name='bids',
        verbose_name=_('ვალუტა')
    )
    estimated_delivery_time = models.IntegerField(
        _('მიწოდების დრო (საათებში)'),
        validators=[MinValueValidator(1)]
    )
    comment = models.TextField(
        _('კომენტარი'),
        blank=True,
        null=True,
        max_length=500
    )
    contact_person = models.CharField(
        _('საკონტაქტო პირი'),
        max_length=100
    )
    contact_phone = models.CharField(
        _('საკონტაქტო ტელეფონი'),
        max_length=20
    )
    external_user_id = models.CharField(
        _('გარე მომხმარებლის ID'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('ID from the external platform to identify the specific broker')
    )
    status = models.CharField(
        _('სტატუსი'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(
        _('შექმნის თარიღი'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('განახლების თარიღი'),
        auto_now=True
    )
    
    # Soft delete fields
    is_deleted = models.BooleanField(
        _('წაშლილია'),
        default=False
    )
    deleted_at = models.DateTimeField(
        _('წაშლის თარიღი'),
        null=True,
        blank=True
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_bids',
        verbose_name=_('წაშალა')
    )
    
    objects = BidManager()
    
    class Meta:
        verbose_name = _('ბიდი')
        verbose_name_plural = _('ბიდები')
        db_table = 'bids'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shipment', 'platform', 'status']),
        ]
    
    def __str__(self):
        return f"{self.company_name} - {self.price} {self.currency.code}"
    
    def accept(self):
        """Mark bid as accepted."""
        self.status = 'accepted'
        self.updated_at = timezone.now()
        self.save(update_fields=['status', 'updated_at'])
    
    def reject(self):
        """Mark bid as rejected and cache the parameters."""
        self.status = 'rejected'
        self.updated_at = timezone.now()
        self.save(update_fields=['status', 'updated_at'])
        
        # Cache rejected bid to prevent exact duplicates
        RejectedBidCache.objects.get_or_create(
            shipment=self.shipment,
            platform=self.platform,
            price=self.price,
            estimated_delivery_time=self.estimated_delivery_time,
            currency=self.currency,
            external_user_id=self.external_user_id,
            defaults={'rejected_at': timezone.now()}
        )


class RejectedBidCache(models.Model):
    """
    Cache of rejected bid parameters to prevent exact duplicate resubmissions.
    Stores the combination of: shipment + broker + price + delivery_time + currency
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    shipment = models.ForeignKey(
        'shipments.Shipment',
        on_delete=models.CASCADE,
        related_name='rejected_bid_cache',
        verbose_name=_('განაცხადი')
    )
    platform = models.ForeignKey(
        Platform,
        on_delete=models.CASCADE,
        related_name='rejected_bid_cache',
        verbose_name=_('პლათფორმა')
    )
    price = models.DecimalField(
        _('ფასი'),
        max_digits=10,
        decimal_places=2
    )
    estimated_delivery_time = models.IntegerField(
        _('მიწოდების დრო (საათებში)')
    )
    currency = models.ForeignKey(
        'metadata.Currency',
        on_delete=models.PROTECT,
        related_name='rejected_bid_cache',
        verbose_name=_('ვალუტა')
    )
    external_user_id = models.CharField(
        _('გარე მომხმარებლის ID'),
        max_length=100,
        blank=True,
        null=True,
        help_text=_('ID from the external platform to identify the specific broker')
    )
    rejected_at = models.DateTimeField(
        _('უარყოფის თარიღი'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('უარყოფილი ბიდის კეში')
        verbose_name_plural = _('უარყოფილი ბიდების კეში')
        db_table = 'rejected_bids_cache'
        constraints = [
            models.UniqueConstraint(
                fields=['shipment', 'platform', 'price', 'estimated_delivery_time', 'currency', 'external_user_id'],
                name='unique_rejected_bid'
            )
        ]
    
    def __str__(self):
        return f"Rejected: {self.platform.company_name} - {self.shipment.id}"
