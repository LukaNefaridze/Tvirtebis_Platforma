import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator
from encrypted_model_fields.fields import EncryptedCharField
from .managers import UserManager
from .utils import validate_personal_id, validate_mobile_number


class User(AbstractBaseUser, PermissionsMixin):
    """
    Unified User model for both administrators and cargo owners.
    """
    ROLE_CHOICES = [
        ('admin', _('ადმინისტრატორი')),
        ('client', _('კლიენტი')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    email = models.EmailField(
        _('ელ. ფოსტა'),
        unique=True,
        validators=[EmailValidator()]
    )
    first_name = models.CharField(
        _('სახელი'),
        max_length=100
    )
    last_name = models.CharField(
        _('გვარი'),
        max_length=100
    )
    
    # Client specific fields (nullable)
    personal_id = EncryptedCharField(
        _('პირადი ნომერი'),
        max_length=11,
        unique=True,
        null=True,
        blank=True,
        help_text=_('11-ციფრიანი პირადი ნომერი')
    )
    mobile = models.CharField(
        _('მობილური'),
        max_length=20,
        null=True,
        blank=True,
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
    
    # System fields
    role = models.CharField(
        _('როლი'),
        max_length=50,
        choices=ROLE_CHOICES,
        default='client'
    )
    is_active = models.BooleanField(
        _('აქტიური'),
        default=True
    )
    is_staff = models.BooleanField(
        _('პერსონალი'),
        default=True,
        help_text=_('საჭიროა Django admin-ში შესასვლელად')
    )
    is_superuser = models.BooleanField(
        _('ზედა ადმინი'),
        default=False
    )
    must_change_password = models.BooleanField(
        _('პაროლის შეცვლა საჭიროა'),
        default=False,
        help_text=_('პირველ შესვლაზე უნდა შეიცვალოს პაროლი')
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
    
    # Soft delete fields
    is_deleted = models.BooleanField(
        _('წაშლილია'),
        default=False
    )
    deleted_at = models.DateTimeField(
        _('წაშლის თარიღი'),
        null=True,
        blank=True
    )
    deleted_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_users',
        verbose_name=_('წაშალა')
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
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
        super().clean()
        if self.personal_id:
            validate_personal_id(self.personal_id)
        if self.mobile:
            validate_mobile_number(self.mobile)

    def save(self, *args, **kwargs):
        if self.pk and self.last_login:
            self.last_login_at = self.last_login
            
        self.clean()
        super().save(*args, **kwargs)
