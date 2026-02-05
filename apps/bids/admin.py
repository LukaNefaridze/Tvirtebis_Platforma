from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display, action
from .models import Platform, PlatformAPIKey, Bid, RejectedBidCache
from apps.accounts.models import User


class PlatformAPIKeyInline(TabularInline):
    """Inline display of API keys for a platform."""
    
    model = PlatformAPIKey
    extra = 0
    can_delete = True
    
    fields = ['id', 'key', 'is_active', 'created_at', 'last_used_at']
    readonly_fields = ['id', 'key', 'created_at', 'last_used_at']
    
    verbose_name = _('API გასაღები')
    verbose_name_plural = _('API გასაღებები')


@admin.register(Platform)
class PlatformAdmin(ModelAdmin):
    """Admin interface for Platform model."""
    
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
        (_('სისტემური'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PlatformAPIKeyInline]
    
    actions = ['activate_platforms', 'deactivate_platforms', 'generate_api_key', 'soft_delete_platforms']
    
    def get_actions(self, request):
        """Remove the default delete action - only soft delete is allowed."""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def has_delete_permission(self, request, obj=None):
        """Disable the delete button on individual platform pages."""
        return False
    
    def get_queryset(self, request):
        """Filter out soft-deleted platforms from the admin list."""
        qs = super().get_queryset(request)
        return qs.filter(is_deleted=False)

    @action(description=_('პლათფორმების წაშლა'))
    def soft_delete_platforms(self, request, queryset):
        """
        Soft delete selected platforms and reject their pending bids.
        """
        deleted_count = 0
        bids_rejected_count = 0
        
        for platform in queryset:
            # Reject all pending bids from this platform
            pending_bids = Bid.objects.filter(platform=platform, status='pending')
            for bid in pending_bids:
                bid.reject()
                bids_rejected_count += 1
            
            # Soft delete the platform
            platform.is_deleted = True
            platform.deleted_at = timezone.now()
            platform.deleted_by = request.user
            platform.is_active = False  # Also deactivate
            platform.save()
            
            deleted_count += 1
            
        self.message_user(
            request,
            _(f'{deleted_count} პლათფორმა წაიშალა და {bids_rejected_count} მიმდინარე ბიდი გაუქმდა'),
            messages.SUCCESS
        )
    
    @display(description=_('სტატუსი'))
    def is_active_badge(self, obj):
        if obj.is_active:
            label = _('აქტიური')
            text_color = 'text-emerald-600 dark:text-emerald-400'
        else:
            label = _('გაუქმებული')
            text_color = 'text-rose-600 dark:text-rose-400'
            
        return format_html(
            '<div class="flex justify-center">'
            '<span class="inline-flex items-center justify-center px-3 py-1.5 rounded-md text-xs font-medium bg-gray-100 dark:bg-gray-800 {}" style="min-width: 100px; display: inline-flex; align-items: center;">{}</span>'
            '</div>',
            text_color,
            label
        )
    
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
    def activate_platforms(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f'{updated} პლათფორმა გააქტიურდა'), messages.SUCCESS)
    
    @action(description=_('დეაქტივაცია'))
    def deactivate_platforms(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f'{updated} პლათფორმა დეაქტიურდა'), messages.SUCCESS)
    
    @action(description=_('API გასაღების გენერაცია'))
    def generate_api_key(self, request, queryset):
        """Generate new API keys for selected brokers."""
        api_keys_info = []
        
        for platform in queryset:
            # Generate new API key
            raw_key = PlatformAPIKey.generate_key()
            api_key = PlatformAPIKey(platform=platform)
            api_key.set_key(raw_key)
            api_key.save()
            
            api_keys_info.append((platform.company_name, raw_key))
        
        # Display all keys to admin (one-time only)
        message_parts = ['<strong>API გასაღებები წარმატებით შეიქმნა:</strong><br><br>']
        for company, key in api_keys_info:
            message_parts.append(f'<strong>{company}</strong>:<br><code>{key}</code><br><br>')
        message_parts.append('<em>გთხოვთ გადაუგზავნოთ ეს გასაღებები პლათფორმებს. ისინი აღარ გამოჩნდება ხელახლა!</em>')
        
        self.message_user(request, format_html(''.join(message_parts)), messages.SUCCESS)
    
    def save_model(self, request, obj, form, change):
        """Handle broker save."""
        super().save_model(request, obj, form, change)
        
        # If this is a new broker, show a message about generating API key
        if not change:
            messages.info(
                request,
                _('პლათფორმა შეიქმნა. გამოიყენეთ "API გასაღების გენერაცია" ქმედება API გასაღების შესაქმნელად.')
            )


@admin.register(Bid)
class BidAdmin(ModelAdmin):
    """Admin interface for Bid model."""
    
    list_display = ['id_short', 'shipment_info', 'platform_link', 'company_name', 
                    'price_display', 'estimated_delivery_time', 'status_badge', 'view_details_button', 'created_at']
    list_filter = ['status', 'shipment__user', 'created_at', 'currency']
    search_fields = ['company_name', 'platform__company_name', 'contact_person', 
                     'shipment__pickup_location', 'shipment__delivery_location']
    ordering = ['-created_at']
    actions = ['soft_delete_bids']
    
    def get_actions(self, request):
        """Remove the default delete action - only soft delete is allowed."""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    @action(description=_('ბიდების წაშლა'))
    def soft_delete_bids(self, request, queryset):
        """Soft delete selected bids."""
        count = queryset.count()
        queryset.update(
            is_deleted=True,
            deleted_at=timezone.now(),
            deleted_by=request.user,
            status='rejected'
        )
        self.message_user(
            request,
            _(f'{count} ბიდი წაიშალა'),
            messages.SUCCESS
        )
    
    fieldsets = (
        (_('ძირითადი ინფორმაცია'), {
            'fields': ('shipment', 'platform', 'company_name', 'status')
        }),
        (_('შეთავაზების დეტალები'), {
            'fields': ('price', 'currency', 'estimated_delivery_time', 'comment')
        }),
        (_('საკონტაქტო ინფორმაცია'), {
            'fields': ('contact_person', 'contact_phone')
        }),
        (_('სისტემური ინფორმაცია'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['shipment', 'platform', 'company_name', 'price', 'currency', 
                       'estimated_delivery_time', 'comment', 'contact_person', 
                       'contact_phone', 'status', 'created_at', 'updated_at']
    
    # Disable clickable links - use the explicit "Details" button instead
    list_display_links = None
    
    @display(description=_('ID'), ordering='id')
    def id_short(self, obj):
        """Display ID as plain text (non-clickable)."""
        return str(obj.id)[:8]
    
    @display(description=_('განაცხადი'))
    def shipment_info(self, obj):
        """Display shipment info as plain text (non-clickable)."""
        return str(obj.shipment)
    
    @display(description=_('პლათფორმა'))
    def platform_link(self, obj):
        """Display platform name as plain text (non-clickable to avoid permission issues)."""
        return obj.platform.company_name
    
    @display(description=_('ფასი'))
    def price_display(self, obj):
        return f"{obj.price} {obj.currency.symbol}"
    
    @display(description=_('სტატუსი'))
    def status_badge(self, obj):
        labels = {
            'pending': _('მოლოდინში'),
            'accepted': _('მიღებული'),
            'rejected': _('უარყოფილი'),
        }
        
        text_colors = {
            'pending': 'text-amber-600 dark:text-amber-400',
            'accepted': 'text-green-600 dark:text-green-400',
            'rejected': 'text-red-600 dark:text-red-400',
        }
        
        label = labels.get(obj.status, obj.status)
        text_color = text_colors.get(obj.status, 'text-gray-600 dark:text-gray-400')
        
        return format_html(
            '<div class="flex justify-center">'
            '<span class="inline-flex items-center justify-center px-3 py-1.5 rounded-md text-xs font-medium bg-gray-100 dark:bg-gray-800 {}" style="min-width: 100px; display: inline-flex; align-items: center;">{}</span>'
            '</div>',
            text_color,
            label
        )
    
    @display(description=_('მართვა'))
    def view_details_button(self, obj):
        """Display a button to view bid details."""
        url = reverse('admin:bids_bid_change', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="background-color: #6c757d; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; display: inline-block;">დეტალები</a>',
            url
        )
    
    def get_queryset(self, request):
        """Filter queryset based on user type."""
        qs = super().get_queryset(request)
        
        # Exclude soft-deleted bids
        qs = qs.filter(is_deleted=False)
        
        # If the logged-in user is a regular User (client), show only bids on their shipments
        if not request.user.is_superuser and getattr(request.user, 'role', '') == 'client':
            return qs.filter(shipment__user=request.user)
        
        return qs
    
    def has_add_permission(self, request):
        """Bids can only be created via API."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable the delete button on individual bid pages."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Bids cannot be edited (read-only)."""
        return False
    
    def has_view_permission(self, request, obj=None):
        """Users can view bids on their shipments, AdminUsers can view all."""
        # Admins can view all
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            return True
            
        # Regular users (clients)
        if obj is None:
            return True  # Can view list (filtered by get_queryset)
            
        # Can view only bids on their own shipments
        return obj.shipment.user_id == request.user.pk
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Override change view to show bids as read-only with clear title.
        """
        extra_context = extra_context or {}
        
        # Get the bid object
        obj = self.get_object(request, object_id)
        
        if obj:
            # Show in read-only mode
            extra_context['show_save'] = False
            extra_context['show_save_and_continue'] = False
            extra_context['show_delete_link'] = False
            
            # Set appropriate title based on user role
            if request.user.role == 'client':
                extra_context['title'] = _('ბიდის დეტალები')
            else:
                extra_context['title'] = _('ბიდის ინფორმაცია')
        
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(RejectedBidCache)
class RejectedBidCacheAdmin(ModelAdmin):
    """Admin interface for RejectedBidCache model (read-only)."""
    
    list_display = ['id_short', 'shipment_link', 'platform_link', 'price', 
                    'estimated_delivery_time', 'currency', 'rejected_at']
    list_filter = ['rejected_at', 'currency']
    search_fields = ['platform__company_name', 'shipment__pickup_location']
    ordering = ['-rejected_at']
    
    fields = ['shipment', 'platform', 'price', 'estimated_delivery_time', 'currency', 'rejected_at']
    readonly_fields = ['shipment', 'platform', 'price', 'estimated_delivery_time', 'currency', 'rejected_at']
    
    @display(description=_('ID'))
    def id_short(self, obj):
        return str(obj.id)[:8]
    
    @display(description=_('განაცხადი'))
    def shipment_link(self, obj):
        url = reverse('admin:shipments_shipment_change', args=[obj.shipment.pk])
        return format_html('<a href="{}">{}</a>', url, str(obj.shipment))
    
    @display(description=_('პლათფორმა'))
    def platform_link(self, obj):
        url = reverse('admin:bids_platform_change', args=[obj.platform.pk])
        return format_html('<a href="{}">{}</a>', url, obj.platform.company_name)
    
    def has_add_permission(self, request):
        """Cache entries are created automatically."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Cache entries can only be deleted by superusers or admin users."""
        return request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'
    
    def has_change_permission(self, request, obj=None):
        """Cache entries are read-only."""
        return False
