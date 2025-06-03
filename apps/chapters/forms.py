from django import forms
from .models import Chapter, ChapterMembership, ChapterActivity

class ChapterForm(forms.ModelForm):
    """Form for creating and updating chapters."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only include provincial and municipal chapters in parent chapter choices
        self.fields['parent_chapter'].queryset = Chapter.objects.filter(tier__in=['provincial', 'municipal'])
    
    class Meta:
        model = Chapter
        fields = [
            'name', 'tier', 'municipality', 'province', 'country',
            'description', 'mission_statement', 'established_date',
            'coordinator', 'email', 'phone', 'address',
            'meeting_location', 'meeting_schedule',
            'facebook_page', 'twitter_handle', 'instagram_handle',
            'parent_chapter'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tier': forms.Select(attrs={'class': 'form-control'}),
            'municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'mission_statement': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'established_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'coordinator': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'meeting_location': forms.TextInput(attrs={'class': 'form-control'}),
            'meeting_schedule': forms.TextInput(attrs={'class': 'form-control'}),
            'facebook_page': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter_handle': forms.TextInput(attrs={'class': 'form-control'}),
            'instagram_handle': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_chapter': forms.Select(attrs={'class': 'form-control'}),
        }

class MembershipForm(forms.ModelForm):
    """Form for managing memberships."""
    
    class Meta:
        model = ChapterMembership
        fields = [
            'user', 'role', 'status', 'is_volunteer',
            'volunteer_skills', 'availability', 'committees',
            'notes'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'volunteer_skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'availability': forms.TextInput(attrs={'class': 'form-control'}),
            'committees': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MembershipApplicationForm(forms.ModelForm):
    """Form for membership applications."""
    
    class Meta:
        model = ChapterMembership
        fields = [
            'is_volunteer', 'volunteer_skills', 'availability',
            'committees', 'notes'
        ]
        widgets = {
            'volunteer_skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Please describe any skills you can offer as a volunteer'
            }),
            'availability': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Weekends, Evenings, Flexible'
            }),
            'committees': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Events, Outreach, Fundraising'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any additional information you\'d like to share'
            }),
        }

class ActivityForm(forms.ModelForm):
    """Form for creating and updating activities."""
    
    class Meta:
        model = ChapterActivity
        fields = [
            'title', 'activity_type', 'description', 'objectives',
            'date', 'start_time', 'end_time', 'venue', 'address',
            'online_link', 'target_participants', 'budget',
            'resources_needed'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'activity_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'objectives': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'venue': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'online_link': forms.URLInput(attrs={'class': 'form-control'}),
            'target_participants': forms.NumberInput(attrs={'class': 'form-control'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'resources_needed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }