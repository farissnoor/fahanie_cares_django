from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import ServiceProgram, ServiceApplication, ServiceDisbursement, ServiceImpact, MinistryProgram

class ServiceProgramForm(forms.ModelForm):
    """Form for creating and updating service programs."""
    
    class Meta:
        model = ServiceProgram
        fields = [
            'name', 'program_type', 'description', 'objectives',
            'eligibility_criteria', 'required_documents', 'target_beneficiaries',
            'start_date', 'end_date', 'application_start', 'application_end',
            'total_budget', 'funding_source', 'max_beneficiaries',
            'status', 'coordinator', 'implementing_chapters',
            'partner_agencies', 'partner_organizations',
            'program_guidelines', 'application_form'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'program_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'objectives': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'eligibility_criteria': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'required_documents': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'target_beneficiaries': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'application_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'application_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'funding_source': forms.TextInput(attrs={'class': 'form-control'}),
            'max_beneficiaries': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'coordinator': forms.Select(attrs={'class': 'form-control'}),
            'implementing_chapters': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'partner_agencies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'partner_organizations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class ServiceApplicationForm(forms.ModelForm):
    """Form for service applications."""
    
    beneficiary_is_self = forms.BooleanField(
        required=False,
        initial=True,
        label="I am applying for myself",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = ServiceApplication
        fields = [
            'beneficiary_is_self', 'beneficiary_name', 'beneficiary_relationship',
            'beneficiary_contact', 'household_size', 'household_income',
            'reason_for_application', 'supporting_details', 'supporting_documents'
        ]
        widgets = {
            'beneficiary_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name of beneficiary'
            }),
            'beneficiary_relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Parent, Child, Spouse'
            }),
            'beneficiary_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact number'
            }),
            'household_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'household_income': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Monthly household income'
            }),
            'reason_for_application': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please explain why you are applying for this service'
            }),
            'supporting_details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any additional information that supports your application'
            }),
            'supporting_documents': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.png,.doc,.docx'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make beneficiary fields required if not applying for self
        self.fields['beneficiary_name'].label = "Beneficiary's Name"
        self.fields['beneficiary_relationship'].label = "Relationship to Beneficiary"
        self.fields['beneficiary_contact'].label = "Beneficiary's Contact"

class ServiceAssessmentForm(forms.ModelForm):
    """Form for assessing service applications."""
    
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for rejection (if rejecting)'
        })
    )
    
    class Meta:
        model = ServiceApplication
        fields = [
            'priority_level', 'assessment_notes', 'home_visit_required',
            'home_visit_completed', 'home_visit_report',
            'assistance_amount', 'assistance_description',
            'follow_up_required', 'follow_up_date', 'follow_up_notes'
        ]
        widgets = {
            'priority_level': forms.Select(attrs={'class': 'form-control'}),
            'assessment_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Assessment findings and recommendations'
            }),
            'home_visit_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'home_visit_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'home_visit_report': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Home visit findings'
            }),
            'assistance_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Amount to be provided'
            }),
            'assistance_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description of assistance to be provided'
            }),
            'follow_up_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'follow_up_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'follow_up_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Follow-up instructions'
            })
        }

class ServiceDisbursementForm(forms.ModelForm):
    """Form for service disbursements."""
    
    class Meta:
        model = ServiceDisbursement
        fields = [
            'amount', 'method', 'reference_number',
            'recipient_name', 'recipient_id_type', 'recipient_id_number',
            'scheduled_date', 'notes'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'method': forms.Select(attrs={'class': 'form-control'}),
            'reference_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Check number, transaction ID, etc.'
            }),
            'recipient_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'recipient_id_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Driver\'s License, PhilHealth ID'
            }),
            'recipient_id_number': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes or instructions'
            })
        }

class ServiceImpactForm(forms.ModelForm):
    """Form for service impact reports."""
    
    class Meta:
        model = ServiceImpact
        fields = [
            'report_date', 'period_start', 'period_end',
            'total_beneficiaries', 'direct_beneficiaries', 'indirect_beneficiaries',
            'municipalities_served', 'barangays_served',
            'total_disbursed', 'average_assistance',
            'success_stories', 'challenges_faced', 'lessons_learned',
            'recommendations', 'impact_photos', 'detailed_report'
        ]
        widgets = {
            'report_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_beneficiaries': forms.NumberInput(attrs={'class': 'form-control'}),
            'direct_beneficiaries': forms.NumberInput(attrs={'class': 'form-control'}),
            'indirect_beneficiaries': forms.NumberInput(attrs={'class': 'form-control'}),
            'municipalities_served': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List municipalities served'
            }),
            'barangays_served': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'List barangays served'
            }),
            'total_disbursed': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'average_assistance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'success_stories': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Share success stories from beneficiaries'
            }),
            'challenges_faced': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe challenges encountered'
            }),
            'lessons_learned': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Key lessons learned'
            }),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Recommendations for improvement'
            }),
            'impact_photos': forms.FileInput(attrs={'class': 'form-control'}),
            'detailed_report': forms.FileInput(attrs={'class': 'form-control'})
        }


# Ministry Program Admin Forms

class MinistryProgramForm(forms.ModelForm):
    """Comprehensive form for creating and editing ministry programs"""
    
    class Meta:
        model = MinistryProgram
        fields = [
            'code', 'title', 'description', 'ministry', 'ppa_type', 'status',
            'total_budget', 'allocated_budget', 'estimated_beneficiaries', 'start_date', 'end_date',
            'geographic_coverage', 'implementing_units', 'expected_outcomes', 'priority_level',
            'implementation_strategy', 'key_performance_indicators', 'objectives',
            'partner_agencies', 'funding_source', 'is_featured', 'is_public'
        ]
        
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'e.g., MSSD-2024-001'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Program title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Detailed program description...'
            }),
            'ministry': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
            }),
            'ppa_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
            }),
            'total_budget': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'allocated_budget': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'estimated_beneficiaries': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'placeholder': 'Number of beneficiaries'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'type': 'date'
            }),
            'geographic_coverage': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Geographic areas covered...'
            }),
            'implementing_units': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Responsible implementing units/offices...'
            }),
            'expected_outcomes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Expected program outcomes...'
            }),
            'priority_level': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
            }),
            'implementation_strategy': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Implementation strategy details...'
            }),
            'key_performance_indicators': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'KPIs for monitoring and evaluation...'
            }),
            'objectives': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Program objectives and goals...'
            }),
            'partner_agencies': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Partner agencies and organizations...'
            }),
            'funding_source': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded'
            })
        }

    def clean_total_budget(self):
        budget = self.cleaned_data.get('total_budget')
        ministry = self.cleaned_data.get('ministry')
        
        if budget and budget < 0:
            raise ValidationError("Budget cannot be negative.")
        
        # Ministry-specific budget limits based on research
        ministry_limits = {
            'mssd': Decimal('15000000000.00'),  # ₱15B max for social services
            'mafar': Decimal('8000000000.00'),   # ₱8B max for agriculture
            'mtit': Decimal('5000000000.00'),    # ₱5B max for tourism/trade
        }
        
        if ministry and budget:
            max_budget = ministry_limits.get(ministry, Decimal('1000000000.00'))
            if budget > max_budget:
                raise ValidationError(
                    f"Budget exceeds maximum limit for {ministry.upper()}: ₱{max_budget:,.2f}"
                )
        
        return budget

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise ValidationError("End date must be after start date.")
        
        return cleaned_data


class ProgramSearchForm(forms.Form):
    """Form for searching and filtering programs"""
    
    MINISTRY_CHOICES = [
        ('', 'All Ministries'),
        ('MSSD', 'Ministry of Social Services and Development'),
        ('MAFAR', 'Ministry of Agriculture, Fisheries and Agrarian Reform'),
        ('MTIT', 'Ministry of Trade, Investment and Tourism'),
    ]
    
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('suspended', 'Suspended'),
    ]
    
    PRIORITY_CHOICES = [
        ('', 'All Priorities'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search programs...'
        })
    )
    
    ministry = forms.ChoiceField(
        choices=MINISTRY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority_level = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    budget_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min budget'
        })
    )
    
    budget_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max budget'
        })
    )
    
    is_featured = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class BulkActionForm(forms.Form):
    """Form for bulk operations on programs"""
    
    ACTION_CHOICES = [
        ('', 'Select Action'),
        ('delete', 'Delete Selected'),
        ('activate', 'Set Status to Active'),
        ('suspend', 'Set Status to Suspended'),
        ('feature', 'Mark as Featured'),
        ('unfeature', 'Remove from Featured'),
        ('export', 'Export Selected'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    selected_programs = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    def clean_selected_programs(self):
        selected = self.cleaned_data.get('selected_programs')
        if not selected:
            raise ValidationError("Please select at least one program.")
        
        try:
            program_ids = [int(id) for id in selected.split(',') if id.strip()]
            if not program_ids:
                raise ValidationError("No valid program IDs selected.")
            return program_ids
        except ValueError:
            raise ValidationError("Invalid program IDs.")


class ImportProgramsForm(forms.Form):
    """Form for importing programs from CSV/Excel files"""
    
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        }),
        help_text="Upload CSV or Excel file with program data"
    )
    
    overwrite_existing = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Overwrite existing programs with same code"
    )
    
    validate_only = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Validate file without importing (preview mode)"
    )