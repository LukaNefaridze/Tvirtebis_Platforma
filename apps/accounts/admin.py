from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.urls import reverse
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin
from unfold.decorators import display, action
from .models import AdminUser, User
from .utils import generate_temporary_password, mask_personal_id


def get_environment(request):
    """Return environment badge for Unfold."""
    return "prod"


def dashboard_callback(request, context):
    """Dashboard customization callback."""
    return context


@admin.register(AdminUser)
class AdminUserAdmin(ModelAdmin, BaseUserAdmin):
    """Admin interface for AdminUser model."""
    
    list_display = ['email', 'get_full_name', 'role', 'is_active_badge', 'is_superuser', 'created_at', 'last_login_at']
    list_filter = ['is_active', 'is_superuser', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('პირადი ინფორმაცია'), {
            'fields': ('first_name', 'last_name', 'role')
        }),
        (_('ნებართვები'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('მნიშვნელოვანი თარიღები'), {
            'fields': ('last_login_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_active', 'is_superuser'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login_at']
    
    @display(description=_('სრული სახელი'))
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    @display(description=_('სტატუსი'), label=True)
    def is_active_badge(self, obj):
        return obj.is_active
    
    actions = ['activate_users', 'deactivate_users']
    
    @action(description=_('გააქტიურება'))
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f'{updated} ადმინისტრატორი გააქტიურდა'), messages.SUCCESS)
    
    @action(description=_('დეაქტივაცია'))
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f'{updated} ადმინისტრატორი დეაქტიურდა'), messages.SUCCESS)


@admin.register(User)
class UserAdmin(ModelAdmin):
    """Admin interface for User model."""
    
    list_display = ['email', 'get_full_name', 'mobile', 'company_name', 'is_active_badge', 'must_change_password_badge', 'shipments_count', 'created_at']
    list_filter = ['is_active', 'must_change_password', 'created_at', 'created_by_admin']
    search_fields = ['email', 'first_name', 'last_name', 'mobile', 'company_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (_('ავტორიზაცია'), {
            'fields': ('email', 'password', 'must_change_password')
        }),
        (_('პირადი ინფორმაცია'), {
            'fields': ('first_name', 'last_name', 'personal_id_display', 'mobile')
        }),
        (_('კომპანიის ინფორმაცია'), {
            'fields': ('company_name', 'company_id_number', 'address'),
            'classes': ('collapse',)
        }),
        (_('დამატებითი'), {
            'fields': ('notes', 'is_active'),
        }),
        (_('სისტემური ინფორმაცია'), {
            'fields': ('created_by_admin', 'created_at', 'updated_at', 'last_login_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (_('ავტორიზაცია'), {
            'fields': ('email',)
        }),
        (_('პირადი ინფორმაცია'), {
            'fields': ('first_name', 'last_name', 'personal_id', 'mobile')
        }),
        (_('კომპანიის ინფორმაცია'), {
            'fields': ('company_name', 'company_id_number', 'address'),
            'classes': ('collapse',)
        }),
        (_('დამატებითი'), {
            'fields': ('notes', 'is_active'),
        }),
    )
    
    readonly_fields = ['personal_id_display', 'created_by_admin', 'created_at', 'updated_at', 'last_login_at', 'shipments_count']
    
    actions = ['activate_users', 'deactivate_users', 'reset_password']
    
    @display(description=_('სრული სახელი'))
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    @display(description=_('სტატუსი'), label=True)
    def is_active_badge(self, obj):
        return obj.is_active
    
    @display(description=_('პაროლის შეცვლა'), label=True)
    def must_change_password_badge(self, obj):
        if obj.must_change_password:
            return True
        return False
    
    @display(description=_('პირადი ნომერი'))
    def personal_id_display(self, obj):
        """Display masked personal ID."""
        if obj.personal_id:
            return mask_personal_id(obj.personal_id)
        return '-'
    
    @display(description=_('განაცხადები'))
    def shipments_count(self, obj):
        """Display count of user's shipments."""
        if obj.pk:
            count = obj.shipments.count()
            if count > 0:
                url = reverse('admin:shipments_shipment_changelist') + f'?user__id__exact={obj.pk}'
                return format_html('<a href="{}">{} განაცხადი</a>', url, count)
            return '0 განაცხადი'
        return '-'
    
    def save_model(self, request, obj, form, change):
        """Override save to generate temporary password for new users."""
        if not change:  # New user
            # Generate temporary password
            temp_password = generate_temporary_password()
            obj.set_password(temp_password)
            obj.must_change_password = True
            obj.created_by_admin = request.user if isinstance(request.user, AdminUser) else None
            obj.is_staff = True  # Allow access to admin panel
            
            # Save the user
            super().save_model(request, obj, form, change)
            
            # Display temp password to admin (one-time only)
            message = format_html(
                '<strong>მომხმარებელი წარმატებით შეიქმნა!</strong><br>'
                'ელ. ფოსტა: <code>{}</code><br>'
                'დროებითი პაროლი: <code>{}</code><br>'
                '<em>გთხოვთ გადაუგზავნოთ ეს მონაცემები მომხმარებელს. პაროლი აღარ გამოჩნდება ხელახლა!</em>',
                obj.email,
                temp_password
            )
            self.message_user(request, message, messages.SUCCESS)
        else:
            super().save_model(request, obj, form, change)
    
    def get_fieldsets(self, request, obj=None):
        """Use different fieldsets for add vs change."""
        if not obj:  # Adding new user
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)
    
    @action(description=_('გააქტიურება'))
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _(f'{updated} მომხმარებელი გააქტიურდა'), messages.SUCCESS)
    
    @action(description=_('დეაქტივაცია'))
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _(f'{updated} მომხმარებელი დეაქტიურდა'), messages.SUCCESS)
    
    @action(description=_('პაროლის გადაყენება'))
    def reset_password(self, request, queryset):
        """Generate new temporary passwords for selected users."""
        reset_info = []
        
        for user in queryset:
            temp_password = generate_temporary_password()
            user.set_password(temp_password)
            user.must_change_password = True
            user.save(update_fields=['password', 'must_change_password'])
            reset_info.append((user.email, temp_password))
        
        # Display all passwords to admin
        message_parts = ['<strong>პაროლები წარმატებით გადაყენდა:</strong><br><br>']
        for email, password in reset_info:
            message_parts.append(f'<strong>{email}</strong>: <code>{password}</code><br>')
        message_parts.append('<br><em>გთხოვთ გადაუგზავნოთ ეს მონაცემები მომხმარებლებს. პაროლები აღარ გამოჩნდება ხელახლა!</em>')
        
        self.message_user(request, format_html(''.join(message_parts)), messages.SUCCESS)
    
    def get_queryset(self, request):
        """Filter queryset based on user type."""
        qs = super().get_queryset(request)
        
        # If the logged-in user is a regular User (not AdminUser), show only their own record
        if isinstance(request.user, User):
            return qs.filter(pk=request.user.pk)
        
        return qs
    
    def has_add_permission(self, request):
        """Only AdminUsers can add new users."""
        return isinstance(request.user, AdminUser)
    
    def has_delete_permission(self, request, obj=None):
        """Only AdminUsers can delete users."""
        return isinstance(request.user, AdminUser)
    
    def has_change_permission(self, request, obj=None):
        """Users can change their own data, AdminUsers can change any user."""
        if isinstance(request.user, AdminUser):
            return True
        if isinstance(request.user, User) and obj and obj.pk == request.user.pk:
            # Users can only change limited fields - handled in get_readonly_fields
            return True
        return False
    
    def get_readonly_fields(self, request, obj=None):
        """Restrict fields for regular users."""
        readonly = list(self.readonly_fields)
        
        if isinstance(request.user, User):
            # Regular users can only view most fields, not edit them
            readonly.extend(['email', 'personal_id', 'mobile', 'first_name', 'last_name', 
                           'company_name', 'company_id_number', 'address', 'is_active', 'notes'])
        
        return readonly
