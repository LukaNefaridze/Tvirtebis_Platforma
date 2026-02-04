from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make password fields optional
        self.fields['password1'].required = False
        self.fields['password2'].required = False

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

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply custom style to all password fields
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'custom-password-input'})
            
    class Media:
        css = {
            'all': ('css/custom.css',)
        }
