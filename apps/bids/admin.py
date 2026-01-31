from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.urls import reverse
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display, action
from .models import Broker, BrokerAPIKey, Bid, RejectedBidCache
from apps.accounts.models import AdminUser, User


class BrokerAPIKeyInline(TabularInline):
    """Inline display of API keys for a broker."""
    
    model = BrokerAPIKey
    extra = 0
    can_delete = True
    
    fields = ['id', 'is_active', 'created_at', 'last_used_at']
    readonly_fields = ['id', 'created_at', 'last_used_at']
    
    verbose_name = _('API გასაღები')
    verbose_name_plural = _('API გასაღებები')


@admin.register(Broker)
class BrokerAdmin(ModelAdmin):
    """Admin interface for Broker model."""
    
    list_display = ['company_name', 'contact_person', 'contact_email', 'contact_phone', 
                    'is_active_badge', 'api_keys_count', 'bids_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['company_name', 'contact_email', 'contact_person', 'contact_phone']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('კომპანიის ინფორმაცია'), {
            'fields': ('company_name', 'is_active')
        }),
        (_('საკონტაქტო ინფორმაცია'), {
            'fields': ('contact_person', 'contact_email', 'contact_phone')
        }),
        (_('ინტეგრაცია'), {
            'fields': ('webhook_url',),
            'description': _('URL for receiving bid status notifications (accepted/rejected)')
        }),
        (_('სისტემური'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    inlines = [BrokerAPIKeyInline]
    
    actions = ['activate_brokers', 'deactivate_brokers', 'generate_api_key']
    
    @display(description=_('სტატუსი'), label=True)
    def is_active_badge(self, obj):
        return obj.is_active
    
    @display(description=_('API გასაღებები'))
    def api_keys_count(self, obj):
        total = obj.api_keys.count()
        active = obj.api_keys.filter(is_active=True).count()
        return format_html('{} ({} აქტიური)', total, active)
    
    @display(description=_('ბიდები'))
    def bids_count(self, obj):
        count = obj.bids.count()
        if count > 0:
            url = reverse('admin:bids_bid_changelist') + f'?broker__id__exact={obj.pk}'
            return format_html('<a href="{}">{}</a>', url, count)
        return '0'
    
    @action(description=_('გააქტიურება'))
    def activate_brokers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f'{updated} ბროკერი გააქტიურდა'), messages.SUCCESS)
    
    @action(description=_('დეაქტივაცია'))
    def deactivate_brokers(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f'{updated} ბროკერი დეაქტიურდა'), messages.SUCCESS)
    
    @action(description=_('API გასაღების გენერაცია'))
    def generate_api_key(self, request, queryset):
        """Generate new API keys for selected brokers."""
        api_keys_info = []
        
        for broker in queryset:
            # Generate new API key
            raw_key = BrokerAPIKey.generate_key()
            api_key = BrokerAPIKey(broker=broker)
            api_key.set_key(raw_key)
            api_key.save()
            
            api_keys_info.append((broker.company_name, raw_key))
        
        # Display all keys to admin (one-time only)
        message_parts = ['<strong>API გასაღებები წარმატებით შეიქმნა:</strong><br><br>']
        for company, key in api_keys_info:
            message_parts.append(f'<strong>{company}</strong>:<br><code>{key}</code><br><br>')
        message_parts.append('<em>გთხოვთ გადაუგზავნოთ ეს გასაღებები ბროკერებს. ისინი აღარ გამოჩნდება ხელახლა!</em>')
        
        self.message_user(request, format_html(''.join(message_parts)), messages.SUCCESS)
    
    def save_model(self, request, obj, form, change):
        """Handle broker save."""
        super().save_model(request, obj, form, change)
        
        # If this is a new broker, show a message about generating API key
        if not change:
            messages.info(
                request,
                _('ბროკერი შეიქმნა. გამოიყენეთ "API გასაღების გენერაცია" ქმედება API გასაღების შესაქმნელად.')
            )


@admin.register(Bid)
class BidAdmin(ModelAdmin):
    """Admin interface for Bid model."""
    
    list_display = ['id_short', 'shipment_link', 'broker_link', 'company_name', 
                    'price_display', 'estimated_delivery_time', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at', 'currency']
    search_fields = ['company_name', 'broker__company_name', 'contact_person', 
                     'shipment__pickup_location', 'shipment__delivery_location']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('განაცხადი და ბროკერი'), {
            'fields': ('shipment', 'broker')
        }),
        (_('შეთავაზება'), {
            'fields': ('company_name', 'price', 'currency', 'estimated_delivery_time', 'comment')
        }),
        (_('საკონტაქტო'), {
            'fields': ('contact_person', 'contact_phone')
        }),
        (_('სტატუსი'), {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['shipment', 'broker', 'company_name', 'price', 'currency', 
                       'estimated_delivery_time', 'comment', 'contact_person', 
                       'contact_phone', 'status', 'created_at', 'updated_at']
    
    @display(description=_('ID'))
    def id_short(self, obj):
        return str(obj.id)[:8]
    
    @display(description=_('განაცხადი'))
    def shipment_link(self, obj):
        url = reverse('admin:shipments_shipment_change', args=[obj.shipment.pk])
        return format_html('<a href="{}">{}</a>', url, str(obj.shipment))
    
    @display(description=_('ბროკერი'))
    def broker_link(self, obj):
        url = reverse('admin:bids_broker_change', args=[obj.broker.pk])
        return format_html('<a href="{}">{}</a>', url, obj.broker.company_name)
    
    @display(description=_('ფასი'))
    def price_display(self, obj):
        return f"{obj.price} {obj.currency.symbol}"
    
    @display(description=_('სტატუსი'), label=True)
    def status_badge(self, obj):
        status_map = {
            'pending': True,
            'accepted': 'success',
            'rejected': False
        }
        return status_map.get(obj.status, obj.status)
    
    def get_queryset(self, request):
        """Filter queryset based on user type."""
        qs = super().get_queryset(request)
        
        # If the logged-in user is a regular User, show only bids on their shipments
        if isinstance(request.user, User):
            return qs.filter(shipment__user=request.user)
        
        return qs
    
    def has_add_permission(self, request):
        """Bids can only be created via API."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Bids should not be deleted (keep for audit trail)."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Bids cannot be edited (read-only)."""
        return False
    
    def has_view_permission(self, request, obj=None):
        """Users can view bids on their shipments, AdminUsers can view all."""
        if isinstance(request.user, AdminUser):
            return True
        if isinstance(request.user, User):
            if obj is None:
                return True  # Can view list
            # Can view only bids on their own shipments
            return obj.shipment.user_id == request.user.pk
        return False


@admin.register(RejectedBidCache)
class RejectedBidCacheAdmin(ModelAdmin):
    """Admin interface for RejectedBidCache model (read-only)."""
    
    list_display = ['id_short', 'shipment_link', 'broker_link', 'price', 
                    'estimated_delivery_time', 'currency', 'rejected_at']
    list_filter = ['rejected_at', 'currency']
    search_fields = ['broker__company_name', 'shipment__pickup_location']
    ordering = ['-rejected_at']
    
    fields = ['shipment', 'broker', 'price', 'estimated_delivery_time', 'currency', 'rejected_at']
    readonly_fields = ['shipment', 'broker', 'price', 'estimated_delivery_time', 'currency', 'rejected_at']
    
    @display(description=_('ID'))
    def id_short(self, obj):
        return str(obj.id)[:8]
    
    @display(description=_('განაცხადი'))
    def shipment_link(self, obj):
        url = reverse('admin:shipments_shipment_change', args=[obj.shipment.pk])
        return format_html('<a href="{}">{}</a>', url, str(obj.shipment))
    
    @display(description=_('ბროკერი'))
    def broker_link(self, obj):
        url = reverse('admin:bids_broker_change', args=[obj.broker.pk])
        return format_html('<a href="{}">{}</a>', url, obj.broker.company_name)
    
    def has_add_permission(self, request):
        """Cache entries are created automatically."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Keep cache entries for audit trail."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Cache entries are read-only."""
        return False
