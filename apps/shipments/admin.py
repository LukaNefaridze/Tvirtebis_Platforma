from django.contrib import admin
from django import forms
from django_flatpickr.widgets import DateTimePickerInput
from django_flatpickr.schemas import FlatpickrOptions
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


class ShipmentUserFilter(admin.SimpleListFilter):
    """Filter shipments by the user who made the listing. Admin only."""
    title = _('განმცხადებელი')
    parameter_name = 'applicant'

    def lookups(self, request, model_admin):
        user_ids = Shipment.objects.values_list('user', flat=True).distinct()
        users = User.objects.filter(id__in=user_ids, is_deleted=False).order_by('first_name', 'last_name')
        return [(u.id, str(u)) for u in users]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user_id=self.value())
        return queryset


class BidInline(TabularInline):
    """Inline display of bids for a shipment."""
    
    model = Bid
    extra = 0
    can_delete = False
    
    fields = ['display_id', 'platform_link', 'company_name', 'price_display', 'estimated_delivery_time', 
              'contact_info', 'status_badge', 'created_at', 'actions_buttons']
    readonly_fields = ['display_id', 'platform_link', 'company_name', 'price_display', 'estimated_delivery_time', 
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
    
    def get_queryset(self, request):
        """Filter bids to exclude soft-deleted ones."""
        qs = super().get_queryset(request)
        return qs.filter(is_deleted=False)

    def get_formset(self, request, obj=None, **kwargs):
        """Store request so actions_buttons can hide Accept/Reject for admins."""
        self._request = request
        return super().get_formset(request, obj, **kwargs)

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
        request = getattr(self, '_request', None)
        # Admins and superusers cannot accept or reject bids - show status only
        if request and (request.user.is_superuser or getattr(request.user, 'role', '') == 'admin'):
            return obj.get_status_display()
        if obj.status == 'pending' and obj.shipment.status == 'active':
            accept_url = reverse('admin:shipment_accept_bid', args=[obj.shipment.pk, obj.pk])
            reject_url = reverse('admin:shipment_reject_bid', args=[obj.shipment.pk, obj.pk])
            return format_html(
                '<a href="{}">მიღება</a> | <a href="{}">უარყოფა</a>',
                accept_url, reject_url
            )
        return obj.get_status_display()



class ShipmentAdminForm(forms.ModelForm):
    pickup_date = forms.DateTimeField(
        label=_('ტვირთის აღების თარიღი და დრო'),
        widget=DateTimePickerInput(options=FlatpickrOptions(
            time_24hr=True,
        ), attrs={'class': 'custom-datepicker'}),
        input_formats=['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S']
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'cargo_volume' in self.fields:
            self.fields['cargo_volume'].widget.attrs['min'] = '0'
            self.fields['cargo_volume'].widget.attrs['step'] = '1'

    class Meta:
        model = Shipment
        fields = '__all__'


@admin.register(Shipment)
class ShipmentAdmin(ModelAdmin):
    """Admin interface for Shipment model."""
    
    form = ShipmentAdminForm
    list_display = ['display_id', 'user_name', 'route', 'pickup_date', 'cargo_info', 
                    'transport_type_display', 'currency_display', 'status_badge', 
                    'bids_count_display', 'view_bids_button', 'created_at']

    def get_list_filter(self, request):
        filters = ['status', 'created_at', 'cargo_type', 'transport_type']
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            filters.insert(1, ShipmentUserFilter)
        return filters

    search_fields = ['pickup_location', 'delivery_location', 'user__email', 
                     'user__first_name', 'user__last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('განაცხადის ინფორმაცია'), {
            'fields': ('id', 'user', 'status')
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
    
    readonly_fields = ['id', 'created_at', 'updated_at', 'completed_at', 'cancelled_at', 'selected_bid', 'status']
    inlines = [BidInline]
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Override get_form to remove add/change/delete/view icons from metadata fields.
        """
        form = super().get_form(request, obj, **kwargs)
        metadata_fields = ['cargo_type', 'volume_unit', 'transport_type', 'preferred_currency']
        
        for field_name in metadata_fields:
            if field_name in form.base_fields:
                field = form.base_fields[field_name]
                if hasattr(field.widget, 'can_add_related'):
                    field.widget.can_add_related = False
                if hasattr(field.widget, 'can_change_related'):
                    field.widget.can_change_related = False
                if hasattr(field.widget, 'can_delete_related'):
                    field.widget.can_delete_related = False
                if hasattr(field.widget, 'can_view_related'):
                    field.widget.can_view_related = False
        return form
    
    def get_fieldsets(self, request, obj=None):
        """Hide 'დამატებითი ინფორმაცია' fieldset when adding a new shipment."""
        if obj is None:
            # Add view - show only relevant fieldsets
            return (
                (_('განაცხადის ინფორმაცია'), {
                    'fields': ('user',)  # no status for new shipments
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
            )
        # Change view - show all fieldsets including დამატებითი ინფორმაცია
        return self.fieldsets
    
    def get_inlines(self, request, obj=None):
        """Only show შეთავაზებები (BidInline) for existing shipments."""
        if obj is None:
            return []  # No inlines for add view
        return [BidInline]
    
    actions = ['cancel_shipments', 'reject_all_bids_action']

    def get_actions(self, request):
        """Admins cannot reject bids; hide reject_all_bids_action from them."""
        actions = super().get_actions(request)
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            actions.pop('reject_all_bids_action', None)
        return actions
    
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
        if obj.status == 'active':
            return format_html(
                '<a class="button" href="{}" style="background-color: #417690; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; display: inline-block;">დეტალები</a>',
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
        
        if obj:
            is_client = request.user.role == 'client' and not request.user.is_superuser
            is_active = obj.status == 'active'
            
            # Make read-only for everyone if shipment exists (published)
            extra_context['show_save'] = False
            extra_context['show_save_and_continue'] = False
            
            if is_active:
                if is_client:
                    extra_context['show_delete_link'] = False
                    extra_context['title'] = _('განაცხადის ნახვა და ბიდების მართვა')
                else:
                    # Admins can still delete, but can't save changes
                    extra_context['title'] = _('განაცხადის დეტალები (გამოქვეყნებული)')
            else:
                # Completed/Cancelled
                if is_client:
                    extra_context['show_delete_link'] = False
                extra_context['title'] = _('განაცხადის დეტალები')
        
        return super().change_view(request, object_id, form_url, extra_context)
    
    def accept_bid_view(self, request, shipment_pk, bid_pk):
        """Accept a specific bid. Only the shipment owner (client) can accept; admins cannot."""
        shipment = get_object_or_404(Shipment, pk=shipment_pk)
        bid = get_object_or_404(Bid, pk=bid_pk, shipment=shipment)
        
        # Admins and superusers cannot accept or reject bids
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            messages.error(request, _('ადმინისტრატორებს არ აქვთ ბიდის მიღების ან უარყოფის უფლება.'))
            return redirect('admin:shipments_shipment_change', shipment_pk)
        
        if not self.has_view_permission(request, shipment):
            messages.error(request, _('თქვენ არ გაქვთ ამ მოქმედების უფლება'))
            return redirect('admin:shipments_shipment_changelist')
        
        # Only the shipment owner can accept
        if shipment.user_id != request.user.pk:
            messages.error(request, _('თქვენ არ გაქვთ ამ მოქმედების უფლება'))
            return redirect('admin:shipments_shipment_changelist')
        
        try:
            shipment.mark_completed(bid)
            messages.success(request, _('ბიდი წარმატებით მიიღეთ. განაცხადი დასრულებულია.'))
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect('admin:shipments_shipment_change', shipment_pk)
    
    def reject_bid_view(self, request, shipment_pk, bid_pk):
        """Reject a specific bid. Only the shipment owner (client) can reject; admins cannot."""
        shipment = get_object_or_404(Shipment, pk=shipment_pk)
        bid = get_object_or_404(Bid, pk=bid_pk, shipment=shipment)
        
        # Admins and superusers cannot accept or reject bids
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            messages.error(request, _('ადმინისტრატორებს არ აქვთ ბიდის მიღების ან უარყოფის უფლება.'))
            return redirect('admin:shipments_shipment_change', shipment_pk)
        
        if not self.has_view_permission(request, shipment):
            messages.error(request, _('თქვენ არ გაქვთ ამ მოქმედების უფლება'))
            return redirect('admin:shipments_shipment_changelist')
        
        # Only the shipment owner can reject
        if shipment.user_id != request.user.pk:
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
        Also excludes shipments from soft-deleted users.
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
        
        # Exclude shipments from soft-deleted users
        qs = qs.filter(user__is_deleted=False)
        
        # If the logged-in user is not a superuser/admin, show only their shipments
        if not request.user.is_superuser and request.user.role == 'client':
             return qs.filter(user=request.user)
        
        return qs
    
    def has_add_permission(self, request):
        """Only clients can create shipments, admins cannot."""
        if request.user.is_superuser or getattr(request.user, 'role', '') == 'admin':
            return False
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
        # If shipment exists (is published), make all fields readonly for everyone
        if obj:
            return [field.name for field in self.model._meta.fields]
            
        # Default behavior for admins (creating new shipment)
        readonly = list(self.readonly_fields)
        return readonly
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter user field based on permissions and exclude deleted users."""
        if db_field.name == 'user':
            if not request.user.is_superuser and request.user.role == 'client':
                # Regular users can only select themselves
                kwargs['queryset'] = User.objects.filter(pk=request.user.pk, is_deleted=False)
                kwargs['initial'] = request.user.pk
            else:
                # Admins see all non-deleted users
                kwargs['queryset'] = User.objects.filter(is_deleted=False)
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        css = {
            'all': ('css/custom.css',)
        }
