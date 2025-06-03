from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse

# Import member models
from .member_models import FahanieCaresMember

# Make FahanieCaresMember available when importing from models
__all__ = ['Constituent', 'ConstituentInteraction', 'ConstituentGroup', 'FahanieCaresMember']

class Constituent(models.Model):
    """
    Extended constituent profile information beyond the user account.
    """
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say')
    )
    
    EDUCATION_LEVEL_CHOICES = (
        ('elementary', 'Elementary School'),
        ('high_school', 'High School'),
        ('vocational', 'Vocational School'),
        ('college', 'College'),
        ('graduate', 'Graduate School'),
        ('other', 'Other')
    )
    
    OCCUPATION_TYPE_CHOICES = (
        ('private_sector', 'Private Sector'),
        ('public_sector', 'Public Sector'),
        ('self_employed', 'Self-employed'),
        ('student', 'Student'),
        ('unemployed', 'Unemployed'),
        ('retired', 'Retired'),
        ('homemaker', 'Homemaker'),
        ('other', 'Other')
    )
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='constituent_profile'
    )
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    education_level = models.CharField(max_length=20, choices=EDUCATION_LEVEL_CHOICES, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    occupation_type = models.CharField(max_length=20, choices=OCCUPATION_TYPE_CHOICES, blank=True)
    household_size = models.PositiveSmallIntegerField(null=True, blank=True)
    is_voter = models.BooleanField(default=True)
    voter_id = models.CharField(max_length=50, blank=True)
    voting_center = models.CharField(max_length=255, blank=True)
    alternate_contact = models.CharField(max_length=255, blank=True, help_text="Emergency contact or alternative contact method")
    bio = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='constituent_profiles/', null=True, blank=True)
    interests = models.TextField(blank=True, help_text="Constituent's interests and concerns")
    language_preference = models.CharField(max_length=50, blank=True, default='English')
    
    # Membership and engagement fields
    membership_date = models.DateField(null=True, blank=True)
    last_engagement = models.DateField(null=True, blank=True)
    engagement_level = models.PositiveSmallIntegerField(default=0, help_text="1-10 scale of engagement")
    notes = models.TextField(blank=True)
    is_volunteer = models.BooleanField(default=False)
    volunteer_interests = models.TextField(blank=True)
    
    # Tracking and metadata
    notion_id = models.CharField(max_length=36, blank=True, help_text="Notion database ID for this constituent")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s Profile"
    
    def get_absolute_url(self):
        return reverse('constituent_detail', args=[self.pk])

class ConstituentInteraction(models.Model):
    """
    Record of interactions with constituents for tracking engagements.
    """
    INTERACTION_TYPES = (
        ('call', 'Phone Call'),
        ('meeting', 'In-person Meeting'),
        ('email', 'Email Exchange'),
        ('social', 'Social Media'),
        ('event', 'Event Attendance'),
        ('referral', 'Service Referral'),
        ('volunteer', 'Volunteer Activity'),
        ('donation', 'Donation/Contribution'),
        ('other', 'Other')
    )
    
    INTERACTION_OUTCOMES = (
        ('resolved', 'Issue Resolved'),
        ('in_progress', 'In Progress'),
        ('follow_up', 'Follow-up Required'),
        ('referred', 'Referred to Agency'),
        ('no_action', 'No Action Required'),
        ('other', 'Other')
    )
    
    constituent = models.ForeignKey(
        Constituent, 
        on_delete=models.CASCADE, 
        related_name='interactions'
    )
    staff_member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='constituent_interactions'
    )
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    date = models.DateTimeField()
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    outcome = models.CharField(max_length=20, choices=INTERACTION_OUTCOMES, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    
    # Tracking and metadata
    notion_id = models.CharField(max_length=36, blank=True, help_text="Notion database ID for this interaction")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.interaction_type} with {self.constituent.user.get_full_name()} on {self.date.strftime('%Y-%m-%d')}"

class ConstituentGroup(models.Model):
    """
    Groups of constituents for targeted communication and management.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(Constituent, related_name='groups')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_constituent_groups'
    )
    is_active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True, max_length=100)
    
    # Tracking and metadata
    notion_id = models.CharField(max_length=36, blank=True, help_text="Notion database ID for this group")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('constituent_group_detail', args=[self.slug])