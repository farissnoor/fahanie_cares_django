from django import forms
from .models import NotificationPreference, NotificationType, NotificationChannel


class NotificationPreferenceForm(forms.ModelForm):
    """Form for user notification preferences."""
    
    # Channel preferences
    email_enabled = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'mr-2'}),
        label='Email Notifications'
    )
    in_app_enabled = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'mr-2'}),
        label='In-App Notifications'
    )
    push_enabled = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'mr-2'}),
        label='Push Notifications'
    )
    sms_enabled = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'mr-2'}),
        label='SMS Notifications'
    )
    
    class Meta:
        model = NotificationPreference
        fields = [
            'email_enabled', 'in_app_enabled', 'push_enabled', 'sms_enabled',
            'digest_frequency', 'quiet_hours_start', 'quiet_hours_end', 'timezone'
        ]
        widgets = {
            'digest_frequency': forms.Select(attrs={'class': 'form-control'}),
            'quiet_hours_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'quiet_hours_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'timezone': forms.Select(attrs={'class': 'form-control'}),
        }


class NotificationTypePreferenceForm(forms.Form):
    """Form for setting notification type preferences."""
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Get user's current preferences
        try:
            preferences = user.notification_preferences
            enabled_types = preferences.enabled_types
        except AttributeError:
            enabled_types = {}
        
        # Create a checkbox for each notification type
        for choice in NotificationType.choices:
            field_name = f'type_{choice[0]}'
            self.fields[field_name] = forms.BooleanField(
                required=False,
                label=choice[1],
                initial=enabled_types.get(choice[0], True),
                widget=forms.CheckboxInput(attrs={'class': 'mr-2'})
            )
    
    def save(self, user):
        """Save the notification type preferences."""
        preferences, created = NotificationPreference.objects.get_or_create(user=user)
        
        enabled_types = {}
        for choice in NotificationType.choices:
            field_name = f'type_{choice[0]}'
            enabled_types[choice[0]] = self.cleaned_data.get(field_name, True)
        
        preferences.enabled_types = enabled_types
        preferences.save()
        return preferences


class NotificationFilterForm(forms.Form):
    """Form for filtering notifications."""
    
    type = forms.ChoiceField(
        choices=[('', 'All Types')] + NotificationType.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('unread', 'Unread'),
            ('read', 'Read'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        choices=[
            ('', 'All Priorities'),
            ('urgent', 'Urgent'),
            ('high', 'High'),
            ('normal', 'Normal'),
            ('low', 'Low'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )