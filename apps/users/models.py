from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom user model for #FahanieCares application.
    Extends Django's built-in AbstractUser to add custom fields.
    """
    USER_TYPES = (
        ('constituent', 'Constituent'),
        ('member', 'Member'),
        ('chapter_member', 'Chapter Member'),
        ('coordinator', 'Chapter Coordinator'),
        ('staff', 'Parliamentary Office Staff'),
        ('mp', 'MP'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='constituent')
    middle_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    municipality = models.CharField(max_length=100, blank=True)
    chapter_id = models.CharField(max_length=50, blank=True)
    is_approved = models.BooleanField(default=False)
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, blank=True, help_text="TOTP secret for MFA")
    mfa_backup_codes = models.TextField(blank=True, help_text="Comma-separated backup codes")
    notion_id = models.CharField(max_length=36, blank=True, help_text="Notion database ID for this user")
    
    def is_staff_or_above(self):
        """Check if user is staff or MP."""
        return self.user_type in ['staff', 'mp']
    
    def is_coordinator_or_above(self):
        """Check if user is a coordinator, staff, or MP."""
        return self.user_type in ['coordinator', 'staff', 'mp']
    
    def is_member_or_above(self):
        """Check if user is a registered member or higher role."""
        return self.user_type in ['member', 'chapter_member', 'coordinator', 'staff', 'mp']
    
    def __str__(self):
        return self.username