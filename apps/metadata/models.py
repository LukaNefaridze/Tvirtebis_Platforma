import uuid
from django.db import models
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from .managers import ActiveMetadataManager


class BaseMetadata(models.Model):
    """
    Abstract base model for all metadata types (cargo, transport, volume units, currency).
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        _('დასახელება'),
        max_length=100
    )
    is_active = models.BooleanField(
        _('აქტიური'),
        default=True,
        help_text=_('არააქტიური ჩანაწერები არ ჩანს dropdown-ებში')
    )
    sort_order = models.IntegerField(
        _('დალაგების რიგითობა'),
        default=0,
        help_text=_('ნაკლები რიცხვი = უფრო ადრე გამოჩნდება')
    )
    created_at = models.DateTimeField(
        _('შექმნის თარიღი'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('განახლების თარიღი'),
        auto_now=True
    )

    objects = models.Manager()  # Default manager
    active = ActiveMetadataManager()  # Active only manager

    class Meta:
        abstract = True
        ordering = ['sort_order', 'name']

    def save(self, *args, **kwargs):
        if self._state.adding:
            ModelClass = self.__class__
            if ModelClass.objects.filter(sort_order=self.sort_order).exists():
                self.sort_order += 1
                ModelClass.objects.filter(
                    sort_order__gte=self.sort_order
                ).update(sort_order=F('sort_order') + 1)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CargoType(BaseMetadata):
    """Cargo type (e.g., food products, construction materials, furniture, electronics)."""
    
    class Meta:
        verbose_name = _('ტვირთის ტიპი')
        verbose_name_plural = _('ტვირთის ტიპები')
        db_table = 'cargo_types'


class TransportType(BaseMetadata):
    """Transport type (e.g., tent, refrigerator, container)."""
    
    class Meta:
        verbose_name = _('ტრანსპორტის ტიპი')
        verbose_name_plural = _('ტრანსპორტის ტიპები')
        db_table = 'transport_types'


class VolumeUnit(BaseMetadata):
    """Volume unit (e.g., kilogram, ton, cubic meter)."""
    
    abbreviation = models.CharField(
        _('შემოკლება'),
        max_length=10,
        help_text=_('მაგ: კგ, ტ, მ³')
    )
    
    class Meta:
        verbose_name = _('მოცულობის ერთეული')
        verbose_name_plural = _('მოცულობის ერთეულები')
        db_table = 'volume_units'
    
    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class Currency(BaseMetadata):
    """Currency (e.g., GEL, USD, EUR)."""
    
    code = models.CharField(
        _('კოდი'),
        max_length=3,
        unique=True,
        help_text=_('ISO 4217 კოდი, მაგ: GEL, USD, EUR')
    )
    symbol = models.CharField(
        _('სიმბოლო'),
        max_length=5,
        help_text=_('მაგ: ₾, $, €')
    )
    
    class Meta:
        verbose_name = _('ვალუტა')
        verbose_name_plural = _('ვალუტები')
        db_table = 'currencies'
    
    def __str__(self):
        return f"{self.code} ({self.symbol})"
