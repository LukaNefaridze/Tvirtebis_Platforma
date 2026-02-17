from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from apps.admin_mixins import SafeAdminMixin
from .models import CargoType, TransportType, VolumeUnit, Currency


class BaseMetadataAdmin(SafeAdminMixin, ModelAdmin):
    """Base admin class for metadata models."""
    
    list_display = ['name', 'sort_order']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    list_editable = ['sort_order']
    ordering = ['sort_order', 'name']

    def _is_admin_or_superuser(self, request):
        return request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'

    def has_module_permission(self, request):
        """Hide metadata app from admin index for client users."""
        return self._is_admin_or_superuser(request)

    def has_view_permission(self, request, obj=None):
        return self._is_admin_or_superuser(request)

    def has_add_permission(self, request):
        return self._is_admin_or_superuser(request)

    def has_change_permission(self, request, obj=None):
        return self._is_admin_or_superuser(request)
    
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
        """Prevent deletion for clients and if used in active shipments (Superusers can always delete)."""
        if not self._is_admin_or_superuser(request):
            return False

        if request.user.is_superuser:
            return True

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
    
    list_display = ['name', 'abbreviation', 'sort_order']
    
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
    
    list_display = ['code', 'name', 'symbol', 'sort_order']
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
