from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.urls import reverse, path
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseRedirect
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display, action
from .models import Shipment
from apps.bids.models import Bid
from apps.accounts.models import AdminUser, User


class BidInline(TabularInline):
    """Inline display of bids for a shipment."""
    
    model = Bid
    extra = 0
    can_delete = False
    
    fields = ['broker_link', 'company_name', 'price_display', 'estimated_delivery_time', 
              'contact_info', 'status_badge', 'created_at', 'actions_buttons']
    readonly_fields = ['broker_link', 'company_name', 'price_display', 'estimated_delivery_time', 
                       'contact_info', 'status_badge', 'created_at', 'actions_buttons']
    
    verbose_name = _('შეთავაზება')
    verbose_name_plural = _('შეთავაზებები')
    
    def has_add_permission(self, request, obj=None):
        """Bids can only be created via API."""
        return False
    
    @display(description=_('ბროკერი'))
    def broker_link(self, obj):
        if obj.broker:
            url = reverse('admin:bids_broker_change', args=[obj.broker.pk])
            return format_html('<a href="{}">{}</a>', url, obj.broker.company_name)
        return '-'
    
    @display(description=_('ფასი'))
    def price_display(self, obj):
        return f"{obj.price} {obj.currency.symbol}"
    
    @display(description=_('საკონტაქტო'))
    def contact_info(self, obj):
        return format_html('{}<br>{}', obj.contact_person, obj.contact_phone)
    
    @display(description=_('სტატუსი'), label=True)
    def status_badge(self, obj):
        if obj.status == 'pending':
            return True
        elif obj.status == 'accepted':
            return 'success'
        else:  # rejected
            return False
    
    @display(description=_('მოქმედებები'))
    def actions_buttons(self, obj):
        if obj.status == 'pending' and obj.shipment.status == 'active':
            accept_url = reverse('admin:shipment_accept_bid', args=[obj.shipment.pk, obj.pk])
            reject_url = reverse('admin:shipment_reject_bid', args=[obj.shipment.pk, obj.pk])
            return format_html(
                '<a class="button" href="{}">მიღება</a> '
                '<a class="button" href="{}">უარყოფა</a>',
                accept_url, reject_url
            )
        return format_html('<span style="color: #999;">{}</span>', obj.get_status_display())


@admin.register(Shipment)
class ShipmentAdmin(ModelAdmin):
    """Admin interface for Shipment model."""
    
    list_display = ['id_short', 'user_name', 'route', 'pickup_date', 'cargo_info', 
                    'status_badge', 'bids_count_display', 'created_at']
    list_filter = ['status', 'created_at', 'cargo_type', 'transport_type']
    search_fields = ['pickup_location', 'delivery_location', 'user__email', 
                     'user__first_name', 'user__last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('განმცხადებელი'), {
            'fields': ('user',)
        }),
        (_('მარშრუტი და დრო'), {
            'fields': ('pickup_location', 'pickup_date', 'delivery_location')
        }),
        (_('ტვირთის ინფორმაცია'), {
            'fields': ('cargo_type', 'cargo_volume', 'volume_unit', 'transport_type')
        }),
        (_('ფინანსური'), {
            'fields': ('preferred_currency',)
        }),
        (_('დამატებითი'), {
            'fields': ('additional_conditions',),
            'classes': ('collapse',)
        }),
        (_('სტატუსი'), {
            'fields': ('status', 'selected_bid', 'completed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
        (_('სისტემური'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'completed_at', 'cancelled_at', 'selected_bid']
    inlines = [BidInline]
    
    actions = ['cancel_shipments', 'reject_all_bids_action']
    
    @display(description=_('ID'))
    def id_short(self, obj):
        return str(obj.id)[:8]
    
    @display(description=_('განმცხადებელი'))
    def user_name(self, obj):
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.get_full_name())
    
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
            'active': True,
            'completed': 'success',
            'cancelled': False
        }
        return status_map.get(obj.status, obj.status)
    
    @display(description=_('ბიდები'))
    def bids_count_display(self, obj):
        total = obj.bids_count
        pending = obj.pending_bids_count
        if pending > 0:
            return format_html('<strong>{}</strong> ({} მოლოდინში)', total, pending)
        return str(total)
    
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
    
    def accept_bid_view(self, request, shipment_pk, bid_pk):
        """Accept a specific bid."""
        shipment = get_object_or_404(Shipment, pk=shipment_pk)
        bid = get_object_or_404(Bid, pk=bid_pk, shipment=shipment)
        
        # Check permissions
        if not self.has_change_permission(request, shipment):
            messages.error(request, _('თქვენ არ გაქვთ ამ მოქმედების უფლება'))
            return redirect('admin:shipments_shipment_change', shipment_pk)
        
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
        
        # Check permissions
        if not self.has_change_permission(request, shipment):
            messages.error(request, _('თქვენ არ გაქვთ ამ მოქმედების უფლება'))
            return redirect('admin:shipments_shipment_change', shipment_pk)
        
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
        """Filter queryset based on user type."""
        qs = super().get_queryset(request)
        
        # If the logged-in user is a regular User, show only their shipments
        if isinstance(request.user, User):
            return qs.filter(user=request.user)
        
        return qs
    
    def has_add_permission(self, request):
        """Both AdminUsers and regular Users can create shipments."""
        return request.user.is_authenticated
    
    def has_change_permission(self, request, obj=None):
        """Users can change their own shipments, AdminUsers can change any."""
        if isinstance(request.user, AdminUser):
            return True
        if isinstance(request.user, User) and obj and obj.user_id == request.user.pk:
            return True
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only AdminUsers can delete shipments."""
        return isinstance(request.user, AdminUser)
    
    def save_model(self, request, obj, form, change):
        """Set user automatically for new shipments."""
        if not change and isinstance(request.user, User):
            obj.user = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """Make status fields readonly."""
        readonly = list(self.readonly_fields)
        
        # Status should be changed via actions, not directly
        if obj:
            readonly.append('status')
        
        return readonly
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter user field based on permissions."""
        if db_field.name == 'user':
            if isinstance(request.user, User):
                # Regular users can only select themselves
                kwargs['queryset'] = User.objects.filter(pk=request.user.pk)
                kwargs['initial'] = request.user.pk
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
