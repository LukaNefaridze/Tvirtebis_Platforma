import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator
from encrypted_model_fields.fields import EncryptedCharField
from .managers import AdminUserManager, UserManager
from .utils import validate_personal_id, validate_mobile_number


class AdminUser(AbstractBaseUser, PermissionsMixin):
    """
    Administrator user model.
    Admins can create and manage regular users, access all shipments, and configure metadata.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    first_name = models.CharField(
        _('სახელი'),
        max_length=100
    )
    last_name = models.CharField(
        _('გვარი'),
        max_length=100
    )
    email = models.EmailField(
        _('ელ. ფოსტა'),
        unique=True,
        validators=[EmailValidator()]
    )
    role = models.CharField(
        _('როლი'),
        max_length=50,
        default='admin'
    )
    is_active = models.BooleanField(
        _('აქტიური'),
        default=True
    )
    is_staff = models.BooleanField(
        _('პერსონალი'),
        default=True
    )
    is_superuser = models.BooleanField(
        _('ზედა ადმინი'),
        default=False
    )
    created_at = models.DateTimeField(
        _('შექმნის თარიღი'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('განახლების თარიღი'),
        auto_now=True
    )
    last_login_at = models.DateTimeField(
        _('ბოლო შესვლა'),
        null=True,
        blank=True
    )
    
    # Fix related_name clashes with User model
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('ჯგუფები'),
        blank=True,
        related_name='admin_users',
        help_text=_('ამ ადმინისტრატორის ჯგუფები')
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('მომხმარებლის უფლებები'),
        blank=True,
        related_name='admin_users',
        help_text=_('ამ ადმინისტრატორის უფლებები')
    )
    
    objects = AdminUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        verbose_name = _('ადმინისტრატორი')
        verbose_name_plural = _('ადმინისტრატორები')
        db_table = 'admins'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_short_name(self):
        return self.first_name
    
    def save(self, *args, **kwargs):
        # Update last_login_at when logging in
        if self.pk and self.last_login:
            self.last_login_at = self.last_login
        super().save(*args, **kwargs)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Regular user model (cargo owners who create shipment listings).
    Users are created by admins and can only manage their own shipments.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    first_name = models.CharField(
        _('სახელი'),
        max_length=100
    )
    last_name = models.CharField(
        _('გვარი'),
        max_length=100
    )
    personal_id = EncryptedCharField(
        _('პირადი ნომერი'),
        max_length=11,
        unique=True,
        help_text=_('11-ციფრიანი პირადი ნომერი')
    )
    email = models.EmailField(
        _('ელ. ფოსტა'),
        unique=True,
        validators=[EmailValidator()]
    )
    mobile = models.CharField(
        _('მობილური'),
        max_length=20,
        help_text=_('+995 XXX XX XX XX ან 5XX XX XX XX')
    )
    company_name = models.CharField(
        _('კომპანიის დასახელება'),
        max_length=200,
        blank=True,
        null=True
    )
    company_id_number = models.CharField(
        _('საიდენტიფიკაციო კოდი'),
        max_length=50,
        blank=True,
        null=True
    )
    address = models.TextField(
        _('მისამართი'),
        blank=True,
        null=True
    )
    notes = models.TextField(
        _('შენიშვნები'),
        blank=True,
        null=True,
        help_text=_('ადმინისთვის დამატებითი ინფორმაცია')
    )
    is_active = models.BooleanField(
        _('აქტიური'),
        default=True
    )
    must_change_password = models.BooleanField(
        _('პაროლის შეცვლა საჭიროა'),
        default=True,
        help_text=_('პირველ შესვლაზე უნდა შეიცვალოს პაროლი')
    )
    created_by_admin = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_users',
        verbose_name=_('შემქმნელი ადმინი')
    )
    is_staff = models.BooleanField(
        _('პერსონალი'),
        default=True,
        help_text=_('საჭიროა Django admin-ში შესასვლელად')
    )
    created_at = models.DateTimeField(
        _('შექმნის თარიღი'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('განახლების თარიღი'),
        auto_now=True
    )
    last_login_at = models.DateTimeField(
        _('ბოლო შესვლა'),
        null=True,
        blank=True
    )
    
    # Fix related_name clashes with AdminUser model
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('ჯგუფები'),
        blank=True,
        related_name='regular_users',
        help_text=_('ამ მომხმარებლის ჯგუფები')
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('მომხმარებლის უფლებები'),
        blank=True,
        related_name='regular_users',
        help_text=_('ამ მომხმარებლის უფლებები')
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'personal_id', 'mobile']
    
    class Meta:
        verbose_name = _('მომხმარებელი')
        verbose_name_plural = _('მომხმარებლები')
        db_table = 'users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_short_name(self):
        return self.first_name
    
    def clean(self):
        """Validate fields before saving."""
        super().clean()
        if self.personal_id:
            validate_personal_id(self.personal_id)
        if self.mobile:
            validate_mobile_number(self.mobile)
    
    def save(self, *args, **kwargs):
        # Update last_login_at when logging in
        if self.pk and self.last_login:
            self.last_login_at = self.last_login
        
        # Validate before saving
        self.clean()
        super().save(*args, **kwargs)
    
    def has_module_perms(self, app_label):
        """Users can access admin for shipments app."""
        if self.is_active and self.is_staff:
            if app_label == 'shipments':
                return True
        return super().has_module_perms(app_label)
    
    def has_perm(self, perm, obj=None):
        """Check if user has specific permission."""
        # Users can only access their own shipments
        if self.is_active and self.is_staff:
            if perm.startswith('shipments.'):
                return True
        return super().has_perm(perm, obj)
