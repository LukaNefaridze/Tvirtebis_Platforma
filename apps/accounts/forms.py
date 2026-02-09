from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.utils.safestring import mark_safe
from .models import User
from .utils import GEORGIAN_PHONE_MAX_LENGTH

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'personal_id', 'mobile', 'company_name', 'company_id_number', 'address')

    class Media:
        css = {
            'all': ('css/custom.css',)
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make password fields optional
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        
        # Set custom help text for password field
        help_texts = [
            "პაროლი უნდა შეიცავდეს მინიმუმ 8 სიმბოლოს.",
            "პაროლი არ უნდა შედგებოდეს მხოლოდ ციფრებისგან.",
            "პაროლი არ უნდა იყოს ფართოდ გავრცელებული (მაგ: password123).",
            "პაროლი არ უნდა ჰგავდეს თქვენს პირად მონაცემებს (სახელი, გვარი, ელ-ფოსტა)."
        ]
        self.fields['password1'].help_text = mark_safe("<br>".join(help_texts))

        for field_name in ['password1', 'password2']:
            if field_name in self.fields:
                # Add custom class to all fields (they are all password inputs)
                current_class = self.fields[field_name].widget.attrs.get('class', '')
                self.fields[field_name].widget.attrs['class'] = f'{current_class} custom-password-input'.strip()
        if 'mobile' in self.fields:
            self.fields['mobile'].widget.attrs['maxlength'] = GEORGIAN_PHONE_MAX_LENGTH

class CustomUserChangeForm(UserChangeForm):
    new_password = forms.CharField(
        label="ახალი პაროლი",
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'custom-password-input',
            'placeholder': 'შეიყვანეთ ახალი პაროლი',
            'autocomplete': 'new-password',
        }),
        help_text="დატოვეთ ცარიელი თუ არ გსურთ პაროლის შეცვლა"
    )

    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the default password field help text link
        if 'password' in self.fields:
            self.fields['password'].help_text = "დაშიფრული პაროლი (ვერ შეიცვლება პირდაპირ)"
        if 'mobile' in self.fields:
            self.fields['mobile'].widget.attrs['maxlength'] = GEORGIAN_PHONE_MAX_LENGTH

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove help text from new password field to hide validation rules by default
        self.fields['new_password1'].help_text = ''
        
        for field in self.fields.values():
            # Add custom class to all fields (they are all password inputs)
            current_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{current_class} custom-password-input'.strip()

    class Media:
        css = {
            'all': ('css/custom.css',)
        }
