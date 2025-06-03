from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class FahanieCaresMember(models.Model):
    """
    Comprehensive member profile for #FahanieCares registration
    """
    
    SEX_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('prefer_not_to_say', 'Prefer not to say')
    )
    
    EDUCATION_CHOICES = (
        ('elementary', 'Elementary School'),
        ('high_school', 'High School'),
        ('vocational', 'Vocational/Technical School'),
        ('some_college', 'Some College'),
        ('bachelors', "Bachelor's Degree"),
        ('masters', "Master's Degree"),
        ('doctorate', 'Doctorate Degree/PhD'),
        ('other', 'Other')
    )
    
    SECTOR_CHOICES = (
        # Vulnerable Sectors
        ('pwd_student', 'PWD College Students'),
        ('solo_parent', 'Solo Parents'),
        ('volunteer_teacher', 'Volunteer Teachers'),
        ('volunteer_health', 'Volunteer Health Workers'),
        ('special_needs', 'Children with Special Needs'),
        ('senior_citizen', 'Senior Citizens'),
        # Women/Mothers and Children
        ('women_mothers', 'Women/Mothers and Children'),
        # Youth
        ('student_scholarship', 'Students in Need of Scholarships'),
        ('student_assistance', 'Students Requiring Educational Assistance'),
    )
    
    ELIGIBILITY_CHOICES = (
        ('none', 'None'),
        ('let_passer', 'LET Passer'),
        ('csc_passer', 'CSC Passer'),
        ('both', 'Both LET and CSC Passer')
    )
    
    # Link to User model
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fahanie_cares_member'
    )
    
    # Application Information
    date_of_application = models.DateField(auto_now_add=True)
    
    # Personal Information
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    age = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(120)])
    sex = models.CharField(max_length=20, choices=SEX_CHOICES)
    
    # Current Address
    address_barangay = models.CharField(max_length=100)
    address_municipality = models.CharField(max_length=100)
    address_province = models.CharField(max_length=100, default='Maguindanao del Sur')
    
    # Voter Registration Address
    voter_address_barangay = models.CharField(max_length=100)
    voter_address_municipality = models.CharField(max_length=100)
    voter_address_province = models.CharField(max_length=100, default='Maguindanao del Sur')
    
    # Sector Information
    sector = models.CharField(max_length=50, choices=SECTOR_CHOICES)
    
    # Education Information
    highest_education = models.CharField(max_length=20, choices=EDUCATION_CHOICES)
    school_graduated = models.CharField(max_length=255, blank=True)
    eligibility = models.CharField(max_length=20, choices=ELIGIBILITY_CHOICES, default='none')
    
    # Volunteer Teacher Information (optional)
    is_volunteer_teacher = models.BooleanField(default=False)
    volunteer_school = models.CharField(max_length=255, blank=True)
    volunteer_service_length = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Length of service as volunteer teacher (e.g., '2 years', '6 months')"
    )
    
    # Additional fields
    is_approved = models.BooleanField(default=False)
    approved_date = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_members'
    )
    
    # Integration fields
    notion_id = models.CharField(max_length=36, blank=True, help_text="Notion database ID")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_of_application']
        verbose_name = '#FahanieCares Member'
        verbose_name_plural = '#FahanieCares Members'
    
    def __str__(self):
        return f"{self.last_name}, {self.first_name} {self.middle_name}"
    
    def get_full_name(self):
        """Return the full name in proper format"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    def get_full_address(self):
        """Return complete current address"""
        return f"{self.address_barangay}, {self.address_municipality}, {self.address_province}"
    
    def get_voter_address(self):
        """Return complete voter registration address"""
        return f"{self.voter_address_barangay}, {self.voter_address_municipality}, {self.voter_address_province}"
    
    def get_sector_display_category(self):
        """Return the main category of the sector"""
        vulnerable_sectors = [
            'pwd_student', 'solo_parent', 'volunteer_teacher', 
            'volunteer_health', 'special_needs', 'senior_citizen'
        ]
        youth_sectors = ['student_scholarship', 'student_assistance']
        
        if self.sector in vulnerable_sectors:
            return "Vulnerable Sectors"
        elif self.sector in youth_sectors:
            return "Youth"
        elif self.sector == 'women_mothers':
            return "Women/Mothers and Children"
        return "Other"