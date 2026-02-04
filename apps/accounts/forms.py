from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
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
    class Meta:
        model = User
        fields = '__all__'
