from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    LegislativeSession, LegislativeMeasure, LegislativeAction,
    Committee, CommitteeMembership, CommitteeHearing,
    PlenarySession, SpeechPrivilege, OversightActivity, VotingRecord
)

User = get_user_model()


class LegislativeMeasureForm(forms.ModelForm):
    """Form for creating or updating legislative measures."""
    
    co_authors = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select co-authors for this measure'
    )
    
    related_measures = forms.ModelMultipleChoiceField(
        queryset=LegislativeMeasure.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        help_text='Select related measures'
    )
    
    class Meta:
        model = LegislativeMeasure
        fields = [
            'session', 'measure_type', 'number', 'title', 'short_title',
            'abstract', 'full_text_url', 'co_authors', 'status', 'priority',
            'filed_date', 'primary_committee', 'secondary_committees',
            'related_measures', 'supersedes', 'beneficiaries',
            'estimated_budget', 'implementation_timeline', 'is_public'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'short_title': forms.TextInput(attrs={'class': 'form-control'}),
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'abstract': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'full_text_url': forms.URLInput(attrs={'class': 'form-control'}),
            'session': forms.Select(attrs={'class': 'form-select'}),
            'measure_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'filed_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'primary_committee': forms.TextInput(attrs={'class': 'form-control'}),
            'secondary_committees': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'beneficiaries': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'estimated_budget': forms.NumberInput(attrs={'class': 'form-control'}),
            'implementation_timeline': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set current session as default
        current_session = LegislativeSession.objects.filter(is_current=True).first()
        if current_session and not self.instance.pk:
            self.fields['session'].initial = current_session


class LegislativeActionForm(forms.ModelForm):
    """Form for recording legislative actions."""
    
    class Meta:
        model = LegislativeAction
        fields = ['action_type', 'description', 'vote_yes', 'vote_no', 'vote_abstain']
        widgets = {
            'action_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'vote_yes': forms.NumberInput(attrs={'class': 'form-control'}),
            'vote_no': forms.NumberInput(attrs={'class': 'form-control'}),
            'vote_abstain': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class CommitteeForm(forms.ModelForm):
    """Form for creating or updating committees."""
    
    class Meta:
        model = Committee
        fields = [
            'name', 'acronym', 'committee_type', 'jurisdiction',
            'parent_committee', 'chairperson', 'vice_chairperson',
            'is_active', 'established_date', 'dissolved_date'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'acronym': forms.TextInput(attrs={'class': 'form-control'}),
            'committee_type': forms.Select(attrs={'class': 'form-select'}),
            'jurisdiction': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parent_committee': forms.Select(attrs={'class': 'form-select'}),
            'chairperson': forms.Select(attrs={'class': 'form-select'}),
            'vice_chairperson': forms.Select(attrs={'class': 'form-select'}),
            'established_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'dissolved_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class CommitteeMembershipForm(forms.ModelForm):
    """Form for committee membership management."""
    
    class Meta:
        model = CommitteeMembership
        fields = ['committee', 'member', 'role', 'start_date', 'end_date', 'is_active']
        widgets = {
            'committee': forms.Select(attrs={'class': 'form-select'}),
            'member': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class CommitteeHearingForm(forms.ModelForm):
    """Form for scheduling committee hearings."""
    
    measures = forms.ModelMultipleChoiceField(
        queryset=LegislativeMeasure.objects.filter(status__in=['filed', 'committee']),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select measures to be discussed'
    )
    
    class Meta:
        model = CommitteeHearing
        fields = [
            'committee', 'hearing_type', 'title', 'description',
            'scheduled_date', 'location', 'measures', 'agenda_url',
            'is_public'
        ]
        widgets = {
            'committee': forms.Select(attrs={'class': 'form-select'}),
            'hearing_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'scheduled_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'agenda_url': forms.URLInput(attrs={'class': 'form-control'}),
        }


class PlenarySessionForm(forms.ModelForm):
    """Form for plenary session management."""
    
    class Meta:
        model = PlenarySession
        fields = [
            'session', 'session_type', 'session_date', 'start_time', 'end_time',
            'order_of_business_url', 'journal_url', 'transcript_url',
            'present_count', 'absent_count', 'key_events'
        ]
        widgets = {
            'session': forms.Select(attrs={'class': 'form-select'}),
            'session_type': forms.Select(attrs={'class': 'form-select'}),
            'session_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'order_of_business_url': forms.URLInput(attrs={'class': 'form-control'}),
            'journal_url': forms.URLInput(attrs={'class': 'form-control'}),
            'transcript_url': forms.URLInput(attrs={'class': 'form-control'}),
            'present_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'absent_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'key_events': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class SpeechPrivilegeForm(forms.ModelForm):
    """Form for recording speeches and privileges."""
    
    class Meta:
        model = SpeechPrivilege
        fields = [
            'plenary_session', 'speech_type', 'title', 'summary',
            'related_measure', 'full_text_url', 'video_url',
            'start_time', 'duration_minutes'
        ]
        widgets = {
            'plenary_session': forms.Select(attrs={'class': 'form-select'}),
            'speech_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'related_measure': forms.Select(attrs={'class': 'form-select'}),
            'full_text_url': forms.URLInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show today's plenary session as default
        today_session = PlenarySession.objects.filter(session_date=timezone.now().date()).first()
        if today_session and not self.instance.pk:
            self.fields['plenary_session'].initial = today_session


class OversightActivityForm(forms.ModelForm):
    """Form for creating or updating oversight activities."""
    
    class Meta:
        model = OversightActivity
        fields = [
            'title', 'activity_type', 'description', 'committee', 'lead_member',
            'target_agency', 'target_program', 'status', 'start_date', 'end_date',
            'key_findings', 'recommendations', 'report_url', 'presentation_url',
            'requires_followup', 'followup_deadline'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'activity_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'committee': forms.Select(attrs={'class': 'form-select'}),
            'lead_member': forms.Select(attrs={'class': 'form-select'}),
            'target_agency': forms.TextInput(attrs={'class': 'form-control'}),
            'target_program': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'key_findings': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'report_url': forms.URLInput(attrs={'class': 'form-control'}),
            'presentation_url': forms.URLInput(attrs={'class': 'form-control'}),
            'followup_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        requires_followup = cleaned_data.get('requires_followup')
        followup_deadline = cleaned_data.get('followup_deadline')
        
        if requires_followup and not followup_deadline:
            raise forms.ValidationError(
                'Follow-up deadline is required when follow-up is marked as required.'
            )
        
        return cleaned_data


class VotingRecordForm(forms.ModelForm):
    """Form for recording votes."""
    
    class Meta:
        model = VotingRecord
        fields = ['vote', 'reasoning']
        widgets = {
            'vote': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'reasoning': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class QuickSearchForm(forms.Form):
    """Quick search form for parliamentary content."""
    
    SEARCH_TYPES = [
        ('all', 'All'),
        ('measures', 'Legislative Measures'),
        ('committees', 'Committees'),
        ('speeches', 'Speeches'),
        ('oversight', 'Oversight Activities'),
    ]
    
    query = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search parliamentary records...'
        })
    )
    
    search_type = forms.ChoiceField(
        choices=SEARCH_TYPES,
        required=False,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-select'})
    )