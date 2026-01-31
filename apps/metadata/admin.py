from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import CargoType, TransportType, VolumeUnit, Currency


class BaseMetadataAdmin(ModelAdmin):
    """Base admin class for metadata models."""
    
    list_display = ['name', 'is_active_badge', 'sort_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    list_editable = ['sort_order']
    ordering = ['sort_order', 'name']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'is_active', 'sort_order')
        }),
        ('თარიღები', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    @display(description='სტატუსი', label=True)
    def is_active_badge(self, obj):
        return obj.is_active
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion if used in active shipments."""
        if obj is None:
            return True
        
        # Check if this metadata is used in any shipments
        if hasattr(obj, 'shipments_cargo'):
            if obj.shipments_cargo.filter(status='active').exists():
                return False
        if hasattr(obj, 'shipments_transport'):
            if obj.shipments_transport.filter(status='active').exists():
                return False
        if hasattr(obj, 'shipments_volume'):
            if obj.shipments_volume.filter(status='active').exists():
                return False
        if hasattr(obj, 'shipments_currency'):
            if obj.shipments_currency.filter(status='active').exists():
                return False
        
        return True


@admin.register(CargoType)
class CargoTypeAdmin(BaseMetadataAdmin):
    """Admin for cargo types."""
    pass


@admin.register(TransportType)
class TransportTypeAdmin(BaseMetadataAdmin):
    """Admin for transport types."""
    pass


@admin.register(VolumeUnit)
class VolumeUnitAdmin(BaseMetadataAdmin):
    """Admin for volume units."""
    
    list_display = ['name', 'abbreviation', 'is_active_badge', 'sort_order', 'created_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'abbreviation', 'is_active', 'sort_order')
        }),
        ('თარიღები', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Currency)
class CurrencyAdmin(BaseMetadataAdmin):
    """Admin for currencies."""
    
    list_display = ['code', 'name', 'symbol', 'is_active_badge', 'sort_order', 'created_at']
    search_fields = ['code', 'name', 'symbol']
    
    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'symbol', 'is_active', 'sort_order')
        }),
        ('თარიღები', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
