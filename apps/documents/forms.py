from django import forms
from .models import Document, DocumentCategory
from django.core.exceptions import ValidationError


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading documents."""
    class Meta:
        model = Document
        fields = ['title', 'description', 'file', 'category', 'tags', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded',
                'placeholder': 'Document title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 border rounded',
                'rows': 3,
                'placeholder': 'Document description'
            }),
            'file': forms.FileInput(attrs={
                'class': 'w-full p-2 border rounded',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.xlsx,.xls'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full p-2 border rounded'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'w-full p-2 border rounded',
                'placeholder': 'Tags (comma-separated)'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'mr-2'
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Check file size (max 10MB)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError('File size must be less than 10MB')
            
            # Check file extension
            allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'xlsx', 'xls']
            ext = file.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(f'File type {ext} is not allowed. Allowed types: {", ".join(allowed_extensions)}')
        
        return file


class DocumentVersionForm(forms.Form):
    """Form for uploading a new version of a document."""
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'w-full p-2 border rounded',
            'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif,.xlsx,.xls'
        })
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full p-2 border rounded',
            'rows': 3,
            'placeholder': 'Changes in this version'
        }),
        required=False
    )


class DocumentSearchForm(forms.Form):
    """Form for searching documents."""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-2 border rounded',
            'placeholder': 'Search documents...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=DocumentCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + list(Document.DOCUMENT_STATUS),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded'
        })
    )
    file_type = forms.ChoiceField(
        choices=[
            ('', 'All Types'),
            ('pdf', 'PDF'),
            ('doc', 'Word Documents'),
            ('image', 'Images'),
            ('excel', 'Excel'),
            ('other', 'Other')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full p-2 border rounded'
        })
    )


class DocumentApprovalForm(forms.Form):
    """Form for approving/rejecting documents."""
    action = forms.ChoiceField(
        choices=[
            ('approve', 'Approve'),
            ('reject', 'Reject'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'mr-2'
        })
    )
    comments = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full p-2 border rounded',
            'rows': 3,
            'placeholder': 'Comments (required for rejection)'
        }),
        required=False
    )
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        comments = cleaned_data.get('comments')
        
        if action == 'reject' and not comments:
            raise ValidationError('Comments are required when rejecting a document.')
        
        return cleaned_data