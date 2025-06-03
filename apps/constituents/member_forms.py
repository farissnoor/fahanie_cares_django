from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from apps.users.models import User
from .member_models import FahanieCaresMember

class FahanieCaresMemberRegistrationForm(UserCreationForm):
    """
    Comprehensive registration form for #FahanieCares members
    """
    # Personal Information
    last_name = forms.CharField(
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Last Name'})
    )
    first_name = forms.CharField(
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'First Name'})
    )
    middle_name = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Middle Name'})
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+639999999999'. Up to 15 digits allowed."
    )
    contact_number = forms.CharField(
        validators=[phone_regex], 
        max_length=20, 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Contact Number'})
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address'})
    )
    
    age = forms.IntegerField(
        min_value=1, 
        max_value=120,
        required=True,
        widget=forms.NumberInput(attrs={'placeholder': 'Age'})
    )
    
    sex = forms.ChoiceField(
        choices=FahanieCaresMember.SEX_CHOICES,
        required=True,
        widget=forms.Select()
    )
    
    # Current Address
    address_barangay = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barangay'})
    )
    address_municipality = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Municipality'})
    )
    address_province = forms.CharField(
        max_length=100,
        initial='Maguindanao del Sur',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Province'})
    )
    
    # Voter Registration Address
    voter_address_barangay = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Voter Registration Barangay'})
    )
    voter_address_municipality = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Voter Registration Municipality'})
    )
    voter_address_province = forms.CharField(
        max_length=100,
        initial='Maguindanao del Sur',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Voter Registration Province'})
    )
    
    # Sector Information
    sector = forms.ChoiceField(
        choices=FahanieCaresMember.SECTOR_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Education Information
    highest_education = forms.ChoiceField(
        choices=FahanieCaresMember.EDUCATION_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    school_graduated = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'School Graduated From'})
    )
    eligibility = forms.ChoiceField(
        choices=FahanieCaresMember.ELIGIBILITY_CHOICES,
        required=True,
        initial='none',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Volunteer Teacher Information
    is_volunteer_teacher = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    volunteer_school = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'School where you volunteer'})
    )
    volunteer_service_length = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2 years, 6 months'})
    )
    
    # Terms and Conditions
    terms = forms.BooleanField(
        required=True,
        label="I agree to the terms and conditions and data privacy policy"
    )
    
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update all widget classes to use Tailwind CSS
        tailwind_classes = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent'
        checkbox_classes = 'rounded border-gray-300 text-primary-600 shadow-sm focus:border-primary-300 focus:ring focus:ring-primary-200 focus:ring-opacity-50'
        
        # Update form widget classes
        for field_name, field in self.fields.items():
            if field_name in ['is_volunteer_teacher', 'terms']:
                field.widget.attrs['class'] = checkbox_classes
            else:
                field.widget.attrs['class'] = tailwind_classes
        
        # Add specific placeholders
        self.fields['username'].widget.attrs['placeholder'] = 'Username (will be used for login)'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'
    
    def clean(self):
        cleaned_data = super().clean()
        is_volunteer = cleaned_data.get('is_volunteer_teacher')
        volunteer_school = cleaned_data.get('volunteer_school')
        volunteer_length = cleaned_data.get('volunteer_service_length')
        
        if is_volunteer:
            if not volunteer_school:
                raise forms.ValidationError("Please specify the school where you volunteer teach.")
            if not volunteer_length:
                raise forms.ValidationError("Please specify your length of service as a volunteer teacher.")
        
        return cleaned_data
    
    def save(self, commit=True):
        # Save User instance
        user = super().save(commit=False)
        user.user_type = 'member'
        user.is_approved = False
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.middle_name = self.cleaned_data['middle_name']
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['contact_number']
        
        if commit:
            user.save()
            
            # Create FahanieCaresMember instance
            member = FahanieCaresMember.objects.create(
                user=user,
                last_name=self.cleaned_data['last_name'],
                first_name=self.cleaned_data['first_name'],
                middle_name=self.cleaned_data['middle_name'],
                contact_number=self.cleaned_data['contact_number'],
                email=self.cleaned_data['email'],
                age=self.cleaned_data['age'],
                sex=self.cleaned_data['sex'],
                address_barangay=self.cleaned_data['address_barangay'],
                address_municipality=self.cleaned_data['address_municipality'],
                address_province=self.cleaned_data['address_province'],
                voter_address_barangay=self.cleaned_data['voter_address_barangay'],
                voter_address_municipality=self.cleaned_data['voter_address_municipality'],
                voter_address_province=self.cleaned_data['voter_address_province'],
                sector=self.cleaned_data['sector'],
                highest_education=self.cleaned_data['highest_education'],
                school_graduated=self.cleaned_data.get('school_graduated', ''),
                eligibility=self.cleaned_data['eligibility'],
                is_volunteer_teacher=self.cleaned_data.get('is_volunteer_teacher', False),
                volunteer_school=self.cleaned_data.get('volunteer_school', ''),
                volunteer_service_length=self.cleaned_data.get('volunteer_service_length', '')
            )
        
        return user


class FahanieCaresMemberUpdateForm(forms.ModelForm):
    """
    Form for updating member information
    """
    class Meta:
        model = FahanieCaresMember
        fields = [
            'last_name', 'first_name', 'middle_name', 'contact_number', 'email',
            'age', 'sex', 'address_barangay', 'address_municipality', 'address_province',
            'voter_address_barangay', 'voter_address_municipality', 'voter_address_province',
            'sector', 'highest_education', 'school_graduated', 'eligibility',
            'is_volunteer_teacher', 'volunteer_school', 'volunteer_service_length'
        ]
        widgets = {
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'sex': forms.Select(attrs={'class': 'form-control'}),
            'address_barangay': forms.TextInput(attrs={'class': 'form-control'}),
            'address_municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'address_province': forms.TextInput(attrs={'class': 'form-control'}),
            'voter_address_barangay': forms.TextInput(attrs={'class': 'form-control'}),
            'voter_address_municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'voter_address_province': forms.TextInput(attrs={'class': 'form-control'}),
            'sector': forms.Select(attrs={'class': 'form-control'}),
            'highest_education': forms.Select(attrs={'class': 'form-control'}),
            'school_graduated': forms.TextInput(attrs={'class': 'form-control'}),
            'eligibility': forms.Select(attrs={'class': 'form-control'}),
            'is_volunteer_teacher': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'volunteer_school': forms.TextInput(attrs={'class': 'form-control'}),
            'volunteer_service_length': forms.TextInput(attrs={'class': 'form-control'}),
        }