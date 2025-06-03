from django import forms
from .models import SavedSearch


class SearchForm(forms.Form):
    """Form for general search functionality."""
    query = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Search constituents, referrals, documents...',
            'x-data': '{}',
            'x-on:input': 'getSuggestions($el.value)',
        })
    )
    module = forms.ChoiceField(
        choices=[
            ('all', 'All Modules'),
            ('constituents', 'Constituents'),
            ('referrals', 'Referrals'),
            ('chapters', 'Chapters'),
            ('services', 'Services'),
            ('documents', 'Documents'),
            ('parliamentary', 'Parliamentary'),
        ],
        required=False,
        initial='all',
        widget=forms.Select(attrs={
            'class': 'form-control px-4 py-2 border rounded-lg',
        })
    )


class AdvancedSearchForm(forms.Form):
    """Form for advanced search with filters."""
    query = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control w-full px-4 py-2 border rounded-lg',
            'placeholder': 'Enter search terms...',
        })
    )
    module = forms.ChoiceField(
        choices=[
            ('constituents', 'Constituents'),
            ('referrals', 'Referrals'),
            ('chapters', 'Chapters'),
            ('services', 'Services'),
            ('documents', 'Documents'),
            ('parliamentary', 'Parliamentary'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control px-4 py-2 border rounded-lg',
            'x-on:change': 'loadModuleFilters($el.value)',
        })
    )
    
    # Dynamic filters based on module
    # Constituent filters
    municipality = forms.CharField(required=False, widget=forms.Select(attrs={
        'class': 'form-control px-4 py-2 border rounded-lg',
    }))
    barangay = forms.CharField(required=False, widget=forms.Select(attrs={
        'class': 'form-control px-4 py-2 border rounded-lg',
    }))
    chapter_member = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input',
    }))
    
    # Referral filters
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
            'class': 'form-control px-4 py-2 border rounded-lg',
        })
    )
    category = forms.CharField(required=False, widget=forms.Select(attrs={
        'class': 'form-control px-4 py-2 border rounded-lg',
    }))
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
            'class': 'form-control px-4 py-2 border rounded-lg',
        })
    )
    
    # Date range filters
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control px-4 py-2 border rounded-lg',
            'type': 'date',
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control px-4 py-2 border rounded-lg',
            'type': 'date',
        })
    )
    
    # Sort options
    sort_by = forms.ChoiceField(
        choices=[
            ('relevance', 'Relevance'),
            ('date_created', 'Date Created'),
            ('date_modified', 'Date Modified'),
            ('alphabetical', 'Alphabetical'),
        ],
        required=False,
        initial='relevance',
        widget=forms.Select(attrs={
            'class': 'form-control px-4 py-2 border rounded-lg',
        })
    )
    sort_order = forms.ChoiceField(
        choices=[
            ('desc', 'Descending'),
            ('asc', 'Ascending'),
        ],
        required=False,
        initial='desc',
        widget=forms.Select(attrs={
            'class': 'form-control px-4 py-2 border rounded-lg',
        })
    )


class SavedSearchForm(forms.ModelForm):
    """Form for saving search criteria."""
    class Meta:
        model = SavedSearch
        fields = ['name', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control w-full px-4 py-2 border rounded-lg',
                'placeholder': 'Name this search...',
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }