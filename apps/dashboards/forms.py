from django import forms
from .models import Report, ScheduledReport, Dashboard, DashboardWidget
from apps.referrals.models import Category


class ReportFilterForm(forms.Form):
    """Form for custom report filters."""
    REPORT_TYPES = [
        ('referrals', 'Referrals Report'),
        ('constituents', 'Constituents Report'),
        ('chapters', 'Chapters Report'),
        ('services', 'Services Report'),
    ]
    
    OUTPUT_FORMATS = [
        ('view', 'View in Browser'),
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'x-on:change': 'updateFilters($el.value)',
        })
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )
    
    # Referral-specific filters
    status = forms.ChoiceField(
        choices=[
            ('', 'All Statuses'),
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )
    
    priority = forms.ChoiceField(
        choices=[
            ('', 'All Priorities'),
            ('low', 'Low'),
            ('normal', 'Normal'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )
    
    # Constituent-specific filters
    municipality = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Municipality',
        })
    )
    
    barangay = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Barangay',
        })
    )
    
    chapter_member = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    
    age_min = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min Age',
        })
    )
    
    age_max = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max Age',
        })
    )
    
    # Output format
    format = forms.ChoiceField(
        choices=OUTPUT_FORMATS,
        initial='view',
        widget=forms.Select(attrs={
            'class': 'form-control',
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate date range
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date must be before end date.")
        
        # Validate age range
        age_min = cleaned_data.get('age_min')
        age_max = cleaned_data.get('age_max')
        
        if age_min and age_max and age_min > age_max:
            raise forms.ValidationError("Minimum age must be less than maximum age.")
        
        return cleaned_data


class ScheduledReportForm(forms.ModelForm):
    """Form for creating scheduled reports."""
    class Meta:
        model = ScheduledReport
        fields = ['name', 'report_type', 'frequency', 'recipients', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Report Name',
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'frequency': forms.Select(attrs={
                'class': 'form-control',
            }),
            'recipients': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '5',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }


class DashboardConfigForm(forms.ModelForm):
    """Form for dashboard configuration."""
    class Meta:
        model = Dashboard
        fields = ['name', 'dashboard_type', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dashboard Name',
            }),
            'dashboard_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }


class DashboardWidgetForm(forms.ModelForm):
    """Form for dashboard widget configuration."""
    class Meta:
        model = DashboardWidget
        fields = ['title', 'widget_type', 'chart_type', 'data_source', 'width', 'height']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Widget Title',
            }),
            'widget_type': forms.Select(attrs={
                'class': 'form-control',
                'x-on:change': 'updateChartTypeOptions($el.value)',
            }),
            'chart_type': forms.Select(attrs={
                'class': 'form-control',
            }),
            'data_source': forms.Select(attrs={
                'class': 'form-control',
            }),
            'width': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '12',
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '100',
                'max': '600',
            }),
        }