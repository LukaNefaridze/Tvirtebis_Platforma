from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.urls import reverse, path
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import get_user_model
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display, action
from .models import Shipment
from apps.bids.models import Bid

User = get_user_model()


class BidInline(TabularInline):
    """Inline display of bids for a shipment."""
    
    model = Bid
    extra = 0
    can_delete = False
    
    fields = ['platform_link', 'company_name', 'price_display', 'estimated_delivery_time', 
              'contact_info', 'status_badge', 'created_at', 'actions_buttons']
    readonly_fields = ['platform_link', 'company_name', 'price_display', 'estimated_delivery_time', 
                       'contact_info', 'status_badge', 'created_at', 'actions_buttons']
    
    verbose_name = _('შეთავაზება')
    verbose_name_plural = _('შეთავაზებები')
    
    def has_add_permission(self, request, obj=None):
        """Bids can only be created via API."""
        return False
    
    def has_view_permission(self, request, obj=None):
        """Users can view bids for their shipments."""
        return True
    
    def has_change_permission(self, request, obj=None):
        """Bids cannot be edited directly in admin."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Bids cannot be deleted directly in admin."""
        return False
    
    @display(description=_('პლათფორმა'))
    def platform_link(self, obj):
        """Display platform name (as text for clients, as link for admins)."""
        if obj.platform:
            # Just return the company name as text - no link to avoid permission issues
            return obj.platform.company_name
        return '-'
    
    @display(description=_('ფასი'))
    def price_display(self, obj):
        return f"{obj.price} {obj.currency.symbol}"
    
    @display(description=_('საკონტაქტო'))
    def contact_info(self, obj):
        return format_html('{}<br>{}', obj.contact_person, obj.contact_phone)
    
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
    
    @display(description=_('მოქმედებები'))
    def actions_buttons(self, obj):
        if obj.status == 'pending' and obj.shipment.status == 'active':
            accept_url = reverse('admin:shipment_accept_bid', args=[obj.shipment.pk, obj.pk])
            reject_url = reverse('admin:shipment_reject_bid', args=[obj.shipment.pk, obj.pk])
            return format_html(
                '<a href="{}">მიღება</a> / <a href="{}">უარყოფა</a>',
                accept_url, reject_url
            )
        return obj.get_status_display()


@admin.register(Shipment)
class ShipmentAdmin(ModelAdmin):
    """Admin interface for Shipment model."""
    
    list_display = ['id_short', 'user_name', 'route', 'pickup_date', 'cargo_info', 
                    'transport_type_display', 'currency_display', 'status_badge', 
                    'bids_count_display', 'view_bids_button', 'created_at']
    list_filter = ['status', 'created_at', 'cargo_type', 'transport_type']
    search_fields = ['pickup_location', 'delivery_location', 'user__email', 
                     'user__first_name', 'user__last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('განაცხადის ინფორმაცია'), {
            'fields': ('user', 'status')
        }),
        (_('მარშრუტი და დრო'), {
            'fields': ('pickup_location', 'pickup_date', 'delivery_location')
        }),
        (_('ტვირთის ინფორმაცია'), {
            'fields': ('cargo_type', 'cargo_volume', 'volume_unit', 'transport_type', 'preferred_currency')
        }),
        (_('დამატებითი პირობები'), {
            'fields': ('additional_conditions',),
            'classes': ('collapse',)
        }),
        (_('დამატებითი ინფორმაცია'), {
            'fields': ('selected_bid', 'completed_at', 'cancelled_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'cancelled_at', 'selected_bid', 'status']
    inlines = [BidInline]
    
    actions = ['cancel_shipments', 'reject_all_bids_action']
    
    # Disable default clickable links - use the explicit "View Bids" button instead
    list_display_links = None
    
    @display(description=_('ID'), ordering='id')
    def id_short(self, obj):
        """Display ID as plain text (non-clickable)."""
        return str(obj.id)[:8]
    
    def user_name(self, obj, request=None):
        """
        Display user name. Only make it clickable for admins.
        """
        # For list display, we need to get the request from the context
        # Since we can't directly access request in list_display methods,
        # we'll return just the name without link for safety
        return obj.user.get_full_name()
    user_name.short_description = _('განმცხადებელი')
    
    @display(description=_('მარშრუტი'))
    def route(self, obj):
        pickup = obj.pickup_location[:30] + '...' if len(obj.pickup_location) > 30 else obj.pickup_location
        delivery = obj.delivery_location[:30] + '...' if len(obj.delivery_location) > 30 else obj.delivery_location
        return f"{pickup} → {delivery}"
    
    @display(description=_('ტვირთი'))
    def cargo_info(self, obj):
        return f"{obj.cargo_volume} {obj.volume_unit.abbreviation} - {obj.cargo_type.name}"
    
    @display(description=_('სტატუსი'), label=True)
    def status_badge(self, obj):
        status_map = {
            'active': 'აქტიური',
            'completed': 'დასრულებული',
            'cancelled': 'გაუქმებული'
        }
        return status_map.get(obj.status, obj.status)
    
    @display(description=_('ბიდები'))
    def bids_count_display(self, obj):
        total = obj.bids_count
        pending = obj.pending_bids_count
        if pending > 0:
            return f"{total} ({pending} მოლოდინში)"
        return str(total)
    
    @display(description=_('ტრანსპორტი'))
    def transport_type_display(self, obj):
        """Display transport type."""
        return obj.transport_type.name
    
    @display(description=_('ვალუტა'))
    def currency_display(self, obj):
        """Display preferred currency."""
        return f"{obj.preferred_currency.code} ({obj.preferred_currency.symbol})"
    
    @display(description=_('მართვა'))
    def view_bids_button(self, obj):
        """Display a button to view and manage bids."""
        url = reverse('admin:shipments_shipment_change', args=[obj.pk])
        if obj.status == 'active' and obj.pending_bids_count > 0:
            return format_html(
                '<a class="button" href="{}" style="background-color: #417690; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; display: inline-block;">ბიდების ნახვა ({})</a>',
                url,
                obj.pending_bids_count
            )
        elif obj.status == 'active':
            return format_html(
                '<a class="button" href="{}" style="background-color: #6c757d; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; display: inline-block;">ნახვა</a>',
                url
            )
        else:
            return format_html(
                '<a class="button" href="{}" style="background-color: #6c757d; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; display: inline-block;">დეტალები</a>',
                url
            )
    
    def get_urls(self):
        """Add custom URLs for bid actions."""
        urls = super().get_urls()
        custom_urls = [
            path('<uuid:shipment_pk>/accept-bid/<uuid:bid_pk>/', 
                 self.admin_site.admin_view(self.accept_bid_view), 
                 name='shipment_accept_bid'),
            path('<uuid:shipment_pk>/reject-bid/<uuid:bid_pk>/', 
                 self.admin_site.admin_view(self.reject_bid_view), 
                 name='shipment_reject_bid'),
        ]
        return custom_urls + urls
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Override change view to ensure clients can see bids and action buttons
        even when the shipment is in read-only mode.
        """
        extra_context = extra_context or {}
        
        # Get the shipment object
        obj = self.get_object(request, object_id)
        
        if obj and request.user.role == 'client':
            if obj.status == 'active':
                # For clients viewing active shipments, show in read-only mode
                # but allow bid actions
                extra_context['show_save'] = False
                extra_context['show_save_and_continue'] = False
                extra_context['show_delete_link'] = False
                extra_context['title'] = _('განაცხადის ნახვა და ბიდების მართვა')
            else:
                # For completed/cancelled shipments
                extra_context['show_save'] = False
                extra_context['show_save_and_continue'] = False
                extra_context['show_delete_link'] = False
                extra_context['title'] = _('განაცხადის დეტალები')
        
        return super().change_view(request, object_id, form_url, extra_context)
    
    def accept_bid_view(self, request, shipment_pk, bid_pk):
        """Accept a specific bid."""
        shipment = get_object_or_404(Shipment, pk=shipment_pk)
        bid = get_object_or_404(Bid, pk=bid_pk, shipment=shipment)
        
        # Check permissions - user must own the shipment
        if not self.has_view_permission(request, shipment):
            messages.error(request, _('თქვენ არ გაქვთ ამ მოქმედების უფლება'))
            return redirect('admin:shipments_shipment_changelist')
        
        # Check if user is the owner
        if shipment.user_id != request.user.pk and not (request.user.is_superuser or request.user.role == 'admin'):
            messages.error(request, _('თქვენ არ გაქვთ ამ მოქმედების უფლება'))
            return redirect('admin:shipments_shipment_changelist')
        
        try:
            shipment.mark_completed(bid)
            messages.success(request, _('ბიდი წარმატებით მიიღეთ. განაცხადი დასრულებულია.'))
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect('admin:shipments_shipment_change', shipment_pk)
    
    def reject_bid_view(self, request, shipment_pk, bid_pk):
        """Reject a specific bid."""
        shipment = get_object_or_404(Shipment, pk=shipment_pk)
        bid = get_object_or_404(Bid, pk=bid_pk, shipment=shipment)
        
        # Check permissions - user must own the shipment
        if not self.has_view_permission(request, shipment):
            messages.error(request, _('თქვენ არ გაქვთ ამ მოქმედების უფლება'))
            return redirect('admin:shipments_shipment_changelist')
        
        # Check if user is the owner
        if shipment.user_id != request.user.pk and not (request.user.is_superuser or request.user.role == 'admin'):
            messages.error(request, _('თქვენ არ გაქვთ ამ მოქმედების უფლება'))
            return redirect('admin:shipments_shipment_changelist')
        
        try:
            bid.reject()
            messages.success(request, _('ბიდი უარყოფილია'))
        except Exception as e:
            messages.error(request, str(e))
        
        return redirect('admin:shipments_shipment_change', shipment_pk)
    
    @action(description=_('განაცხადების გაუქმება'))
    def cancel_shipments(self, request, queryset):
        """Cancel selected shipments."""
        count = 0
        for shipment in queryset.filter(status='active'):
            try:
                shipment.mark_cancelled()
                count += 1
            except ValueError:
                pass
        
        self.message_user(request, _(f'{count} განაცხადი გაუქმდა'), messages.SUCCESS)
    
    @action(description=_('ყველა ბიდის უარყოფა'))
    def reject_all_bids_action(self, request, queryset):
        """Reject all pending bids for selected shipments."""
        count = 0
        for shipment in queryset.filter(status='active'):
            pending_count = shipment.pending_bids_count
            if pending_count > 0:
                shipment.reject_all_pending_bids()
                count += pending_count
        
        self.message_user(request, _(f'{count} ბიდი უარყოფილია'), messages.SUCCESS)
    
    def get_queryset(self, request):
        """
        Filter queryset based on user type.
        """
        qs = super().get_queryset(request)
        
        # Optimize queries
        qs = qs.select_related(
            'user',
            'cargo_type',
            'volume_unit',
            'transport_type',
            'preferred_currency',
            'selected_bid'
        ).prefetch_related(
            'bids',
            'bids__platform',
            'bids__currency'
        )
        
        # If the logged-in user is not a superuser/admin, show only their shipments
        if not request.user.is_superuser and request.user.role == 'client':
             return qs.filter(user=request.user)
        
        return qs
    
    def has_add_permission(self, request):
        """Authenticated users can create shipments."""
        return request.user.is_authenticated
    
    def has_view_permission(self, request, obj=None):
        """
        Users can view their own shipments.
        """
        # Admins have full permissions
        if request.user.is_superuser or request.user.role == 'admin':
            return True
        
        # Regular users: can view their own shipments
        if obj:
            return obj.user_id == request.user.pk
            
        # List view (obj is None): return True so they can see the changelist
        return True
    
    def has_change_permission(self, request, obj=None):
        """
        Users can change their own shipments.
        Prevent clients from editing active (published) shipments.
        """
        # Admins have full permissions
        if request.user.is_superuser or request.user.role == 'admin':
            return True
        
        # Regular users: can change their own shipments ONLY if not active
        if obj:
            # If shipment is active and user is client, deny change permission
            # But they can still view it (has_view_permission returns True)
            if obj.status == 'active' and request.user.role == 'client':
                return False
            return obj.user_id == request.user.pk
            
        # List view (obj is None): return True so they can see the changelist
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Only Admins can delete shipments."""
        return request.user.is_superuser or request.user.role == 'admin'
    
    def save_model(self, request, obj, form, change):
        """Set user automatically for new shipments."""
        if not change and not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """
        Make all fields readonly if shipment is active or if viewing as client.
        Otherwise, return default readonly fields.
        """
        # For clients viewing any existing shipment, make all fields readonly
        if obj and request.user.role == 'client' and not request.user.is_superuser:
            # Return ALL fields as readonly
            return [field.name for field in self.model._meta.fields]
            
        # Default behavior for admins
        readonly = list(self.readonly_fields)
        return readonly
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter user field based on permissions."""
        if db_field.name == 'user':
            if not request.user.is_superuser and request.user.role == 'client':
                # Regular users can only select themselves
                kwargs['queryset'] = User.objects.filter(pk=request.user.pk)
                kwargs['initial'] = request.user.pk
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
