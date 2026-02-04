from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display, action
from .models import User
from .forms import CustomUserCreationForm, CustomUserChangeForm
from .utils import generate_temporary_password, mask_personal_id


def get_environment(request):
    """Return environment badge for Unfold."""
    return "prod"


def dashboard_callback(request, context):
    """Dashboard customization callback."""
    return context


@admin.register(User)
class UserAdmin(ModelAdmin, BaseUserAdmin):
    """Admin interface for Unified User model."""
    
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    
    list_display = ['email', 'get_full_name', 'role', 'is_active_badge', 'is_staff', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['email', 'first_name', 'last_name', 'company_name', 'personal_id']
    ordering = ['-created_at']
    actions = ['reset_password_action']
    
    # Define fieldsets for different sections
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('პირადი ინფორმაცია'), {
            'fields': ('first_name', 'last_name', 'role', 'personal_id', 'mobile')
        }),
        (_('კომპანიის ინფორმაცია'), {
            'fields': ('company_name', 'company_id_number', 'address'),
            'classes': ('collapse',)
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
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login_at']
    
    @display(description=_('სრული სახელი'))
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    @display(description=_('სტატუსი'), label=True)
    def is_active_badge(self, obj):
        return obj.is_active

    def save_model(self, request, obj, form, change):
        """Override save to generate temporary password for new client users."""
        # Check if it's a new user and no password was provided
        # form.cleaned_data.get('password1') checks if password was entered in the form
        password_provided = form.cleaned_data.get('password1') if form and 'password1' in form.cleaned_data else None
        
        if not change and not password_provided:  # New user without password
            # Generate temporary password
            temp_password = generate_temporary_password()
            obj.set_password(temp_password)
            obj.must_change_password = True
            
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

    @action(description=_('პაროლის განახლება (დროებითი პაროლი)'))
    def reset_password_action(self, request, queryset):
        """Reset password for selected users and show temporary password."""
        for user in queryset:
            temp_password = generate_temporary_password()
            user.set_password(temp_password)
            user.must_change_password = True
            user.save()
            
            message = format_html(
                '<strong>მომხმარებლის ({}) პაროლი განახლდა!</strong><br>'
                'ახალი დროებითი პაროლი: <code>{}</code><br>'
                '<em>გთხოვთ გადაუგზავნოთ ეს მონაცემები მომხმარებელს.</em>',
                user.email,
                temp_password
            )
            self.message_user(request, message, messages.SUCCESS)
