from django import forms
from django.contrib.auth import get_user_model
from .models import (
    CommunicationTemplate, CommunicationCampaign, CommunicationMessage,
    AnnouncementPost, CommunicationSettings, ContactFormSubmission,
    PartnershipSubmission, DonationSubmission
)
from apps.constituents.models import ConstituentGroup
from apps.chapters.models import Chapter

User = get_user_model()


class ContactForm(forms.ModelForm):
    """
    Unified contact form for all contact submissions across the site.
    Provides consistent field layout with separate first, middle, last name fields.
    """
    
    class Meta:
        model = ContactFormSubmission
        fields = [
            'first_name', 'middle_name', 'last_name', 
            'email', 'phone_number', 'subject', 'message'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'Enter your first name',
                'required': True,
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'Enter your middle name (optional)',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'Enter your last name',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'Enter your email address',
                'required': True,
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'placeholder': 'Enter your phone number',
                'type': 'tel',
            }),
            'subject': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'required': True,
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'rows': 8,
                'placeholder': 'Enter your message here...',
                'required': True,
            }),
        }
        labels = {
            'first_name': 'First Name',
            'middle_name': 'Middle Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
            'phone_number': 'Phone Number',
            'subject': 'Subject',
            'message': 'Message',
        }
    
    def __init__(self, *args, **kwargs):
        # Allow setting default subject from context
        default_subject = kwargs.pop('default_subject', None)
        super().__init__(*args, **kwargs)
        
        if default_subject and default_subject in dict(ContactFormSubmission.SUBJECT_CHOICES):
            self.fields['subject'].initial = default_subject
    
    def clean_email(self):
        """Validate email format."""
        email = self.cleaned_data.get('email')
        if email:
            # Additional email validation can be added here
            return email.lower().strip()
        return email
    
    def clean_phone_number(self):
        """Clean and validate phone number."""
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove non-numeric characters for storage
            phone = ''.join(filter(str.isdigit, phone))
            if len(phone) < 10:
                raise forms.ValidationError("Please enter a valid phone number with at least 10 digits.")
        return phone


class TemplateForm(forms.ModelForm):
    """
    Form for creating/editing communication templates.
    """
    class Meta:
        model = CommunicationTemplate
        fields = [
            'name', 'template_type', 'category', 'subject', 'content', 'is_active'
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 8}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add placeholder text for template variables
        self.fields['content'].help_text = (
            "You can use variables like {{first_name}}, {{last_name}}, "
            "{{program_name}}, {{chapter_name}}, etc."
        )


class CampaignForm(forms.ModelForm):
    """
    Form for creating/editing communication campaigns.
    """
    target_groups = forms.ModelMultipleChoiceField(
        queryset=ConstituentGroup.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select constituent groups to target"
    )
    
    target_chapters = forms.ModelMultipleChoiceField(
        queryset=Chapter.objects.filter(status='active'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select chapters to target"
    )
    
    custom_recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        help_text="Add specific recipients"
    )
    
    class Meta:
        model = CommunicationCampaign
        fields = [
            'name', 'description', 'template',
            'target_all_constituents', 'target_groups', 'target_chapters',
            'target_user_types', 'custom_recipients',
            'subject', 'content', 'attachments', 'scheduled_time'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 8}),
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'target_user_types': forms.CheckboxSelectMultiple(
                choices=User.USER_TYPES
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Load template content if selected
        if self.instance.template:
            self.fields['subject'].initial = self.instance.template.subject
            self.fields['content'].initial = self.instance.template.content
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate targeting
        if not any([
            cleaned_data.get('target_all_constituents'),
            cleaned_data.get('target_groups'),
            cleaned_data.get('target_chapters'),
            cleaned_data.get('target_user_types'),
            cleaned_data.get('custom_recipients'),
        ]):
            raise forms.ValidationError(
                "Please select at least one targeting option."
            )
        
        return cleaned_data


class MessageComposeForm(forms.ModelForm):
    """
    Form for composing direct messages.
    """
    recipient = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'select2'}),
        help_text="Select recipient"
    )
    
    class Meta:
        model = CommunicationMessage
        fields = ['recipient', 'message_type', 'subject', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default message type
        self.fields['message_type'].initial = 'email'


class AnnouncementForm(forms.ModelForm):
    """
    Form for creating/editing announcements.
    """
    target_chapters = forms.ModelMultipleChoiceField(
        queryset=Chapter.objects.filter(status='active'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select chapters to target (leave empty for all)"
    )
    
    class Meta:
        model = AnnouncementPost
        fields = [
            'title', 'category', 'summary', 'content', 'featured_image',
            'status', 'is_featured', 'is_pinned', 'show_on_homepage',
            'target_all', 'target_chapters', 'target_user_types'
        ]
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 3}),
            'content': forms.Textarea(attrs={'rows': 10}),
            'target_user_types': forms.CheckboxSelectMultiple(
                choices=User.USER_TYPES
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make published_date field if publishing
        if self.instance.pk and self.instance.status == 'published':
            self.fields['published_date'] = forms.DateTimeField(
                required=False,
                widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
                initial=self.instance.published_date
            )


class CommunicationSettingsForm(forms.ModelForm):
    """
    Form for user communication preferences.
    """
    class Meta:
        model = CommunicationSettings
        fields = [
            'email_enabled', 'sms_enabled', 'push_enabled',
            'allow_marketing', 'allow_newsletters', 'allow_event_invites',
            'allow_program_updates', 'referral_notifications',
            'application_notifications', 'chapter_notifications',
            'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
            'preferred_language'
        ]
        widgets = {
            'quiet_hours_start': forms.TimeInput(attrs={'type': 'time'}),
            'quiet_hours_end': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Group fields for better UX
        self.fields['email_enabled'].label = "Email notifications"
        self.fields['sms_enabled'].label = "SMS notifications"
        self.fields['push_enabled'].label = "Push notifications"
        
        self.fields['allow_marketing'].label = "Marketing communications"
        self.fields['allow_newsletters'].label = "Newsletters"
        self.fields['allow_event_invites'].label = "Event invitations"
        self.fields['allow_program_updates'].label = "Program updates"
        
        self.fields['referral_notifications'].label = "Referral status updates"
        self.fields['application_notifications'].label = "Application status updates"
        self.fields['chapter_notifications'].label = "Chapter activities"
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate quiet hours
        if cleaned_data.get('quiet_hours_enabled'):
            start = cleaned_data.get('quiet_hours_start')
            end = cleaned_data.get('quiet_hours_end')
            
            if not start or not end:
                raise forms.ValidationError(
                    "Please specify both start and end times for quiet hours."
                )
        
        return cleaned_data


class PartnershipForm(forms.ModelForm):
    """
    Form for partnership inquiries and applications.
    """
    class Meta:
        model = PartnershipSubmission
        fields = [
            "organization_name", "contact_person", "email", "phone_number", "website",
            "partnership_type", "proposed_collaboration", "resources_offered", "expected_outcomes"
        ]
        widgets = {
            "organization_name": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "Enter organization name",
                "required": True,
            }),
            "contact_person": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "Enter contact person name",
                "required": True,
            }),
            "email": forms.EmailInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "Enter email address",
                "required": True,
            }),
            "phone_number": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "Enter phone number",
                "type": "tel",
            }),
            "website": forms.URLInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "Enter organization website (optional)",
            }),
            "partnership_type": forms.Select(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "required": True,
            }),
            "proposed_collaboration": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "rows": 4,
                "placeholder": "Describe the proposed collaboration or partnership...",
                "required": True,
            }),
            "resources_offered": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "rows": 3,
                "placeholder": "What resources can your organization offer?",
            }),
            "expected_outcomes": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "rows": 3,
                "placeholder": "What outcomes do you expect from this partnership?",
            }),
        }


class DonationForm(forms.ModelForm):
    """
    Form for donation inquiries and pledges.
    """
    class Meta:
        model = DonationSubmission
        fields = [
            "donor_name", "donor_type", "email", "phone_number",
            "donation_type", "amount", "description", "frequency", "preferred_program"
        ]
        widgets = {
            "donor_name": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "Enter your full name",
                "required": True,
            }),
            "donor_type": forms.Select(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "required": True,
            }),
            "email": forms.EmailInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "Enter email address",
                "required": True,
            }),
            "phone_number": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "Enter phone number",
                "type": "tel",
            }),
            "donation_type": forms.Select(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "required": True,
            }),
            "amount": forms.NumberInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "Enter amount (for monetary donations)",
                "step": "0.01",
                "min": "0",
            }),
            "description": forms.Textarea(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "rows": 4,
                "placeholder": "Describe your donation or intended use...",
                "required": True,
            }),
            "frequency": forms.Select(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "required": True,
            }),
            "preferred_program": forms.TextInput(attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500",
                "placeholder": "Specific program to support (optional)",
            }),
        }

