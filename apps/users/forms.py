from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import User

class UserRegistrationForm(UserCreationForm):
    """
    Custom registration form for #FahanieCares.
    Extends Django's UserCreationForm to add custom fields.
    """
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = forms.CharField(validators=[phone_regex], max_length=15, required=True)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=True)
    municipality = forms.CharField(max_length=100, required=True)
    terms = forms.BooleanField(required=True)
    
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'username', 'email', 'phone_number',
            'address', 'municipality', 'password1', 'password2'
        )
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'member'  # Set user as member by default
        user.is_approved = False  # Require approval before full access
        
        if commit:
            user.save()
            
        return user