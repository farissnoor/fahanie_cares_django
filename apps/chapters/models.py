from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse

class Chapter(models.Model):
    """
    Chapter model for #FahanieCares organization units.
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('pending', 'Pending Approval'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    )
    
    TIER_CHOICES = (
        ('provincial', 'Provincial Chapter'),
        ('municipal', 'Municipal/City Chapter'),
    )
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES)
    municipality = models.CharField(max_length=100)
    province = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Philippines')
    
    # Chapter details
    description = models.TextField(blank=True)
    mission_statement = models.TextField(blank=True)
    established_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Leadership
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='coordinated_chapters'
    )
    assistant_coordinators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='assistant_coordinated_chapters',
        blank=True
    )
    
    # Contact information
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    meeting_location = models.TextField(blank=True)
    meeting_schedule = models.CharField(max_length=200, blank=True)
    
    # Social media
    facebook_page = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=50, blank=True)
    instagram_handle = models.CharField(max_length=50, blank=True)
    
    # Parent-child relationship for hierarchical structure
    parent_chapter = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_chapters'
    )
    
    # Tracking
    member_count = models.PositiveIntegerField(default=0)
    volunteer_count = models.PositiveIntegerField(default=0)
    activity_count = models.PositiveIntegerField(default=0)
    notion_id = models.CharField(max_length=36, blank=True, help_text="Notion database ID")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chapters_approved'
    )
    
    class Meta:
        ordering = ['tier', 'name']
        verbose_name = 'Chapter'
        verbose_name_plural = 'Chapters'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.get_tier_display()})"
    
    def get_absolute_url(self):
        return reverse('chapter_detail', args=[self.slug])
    
    def activate(self, approved_by):
        """Activate a pending chapter."""
        self.status = 'active'
        self.approved_at = timezone.now()
        self.approved_by = approved_by
        self.save()
    
    def update_member_count(self):
        """Update the member count based on actual memberships."""
        self.member_count = self.memberships.filter(
            status='active',
            end_date__isnull=True
        ).count()
        self.save(update_fields=['member_count'])


class ChapterMembership(models.Model):
    """
    Membership records for chapter members.
    """
    ROLE_CHOICES = (
        ('member', 'Member'),
        ('volunteer', 'Volunteer'),
        ('coordinator', 'Coordinator'),
        ('assistant_coordinator', 'Assistant Coordinator'),
        ('secretary', 'Secretary'),
        ('treasurer', 'Treasurer'),
        ('auditor', 'Auditor'),
        ('committee_member', 'Committee Member'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('pending', 'Pending Approval'),
    )
    
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chapter_memberships'
    )
    
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='member')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Membership details
    joined_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    membership_number = models.CharField(max_length=50, blank=True)
    
    # Volunteer information
    is_volunteer = models.BooleanField(default=False)
    volunteer_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    volunteer_skills = models.TextField(blank=True)
    availability = models.CharField(max_length=200, blank=True)
    
    # Committee assignments
    committees = models.TextField(blank=True, help_text="Comma-separated list of committees")
    
    # Tracking
    activities_attended = models.PositiveIntegerField(default=0)
    activities_organized = models.PositiveIntegerField(default=0)
    referrals_made = models.PositiveIntegerField(default=0)
    
    # Meta
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='memberships_approved'
    )
    
    def generate_membership_number(self):
        """Generate a unique membership number."""
        import time
        chapter_code = self.chapter.municipality[:3].upper()
        timestamp = str(int(time.time()))[-4:]
        self.membership_number = f"FCM-{chapter_code}-{timestamp}"
        return self.membership_number
    
    class Meta:
        unique_together = ('chapter', 'user')
        ordering = ['-joined_date']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.chapter.name} ({self.get_role_display()})"
    
    def approve(self, approved_by):
        """Approve a pending membership."""
        self.status = 'active'
        self.approved_at = timezone.now()
        self.approved_by = approved_by
        
        # Generate membership number if not exists
        if not self.membership_number:
            self.generate_membership_number()
        
        self.save()
        
        # Update chapter member count
        self.chapter.update_member_count()


class ChapterActivity(models.Model):
    """
    Activities organized by chapters.
    """
    ACTIVITY_TYPES = (
        ('meeting', 'Regular Meeting'),
        ('outreach', 'Community Outreach'),
        ('fundraising', 'Fundraising Event'),
        ('training', 'Training/Workshop'),
        ('social', 'Social Gathering'),
        ('volunteer', 'Volunteer Activity'),
        ('campaign', 'Campaign Event'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    )
    
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    
    # Activity details
    title = models.CharField(max_length=200)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    objectives = models.TextField(blank=True)
    
    # Schedule
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    
    # Location
    venue = models.CharField(max_length=200)
    address = models.TextField()
    online_link = models.URLField(blank=True, help_text="For virtual activities")
    
    # Organization
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organized_activities'
    )
    co_organizers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='co_organized_activities',
        blank=True
    )
    
    # Participation
    target_participants = models.PositiveIntegerField(default=0)
    actual_participants = models.PositiveIntegerField(default=0)
    member_attendees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ActivityAttendance',
        related_name='attended_activities'
    )
    
    # Resources
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    resources_needed = models.TextField(blank=True)
    
    # Documentation
    report = models.TextField(blank=True)
    photos = models.FileField(upload_to='chapter_activities/', blank=True, null=True)
    materials = models.FileField(upload_to='chapter_materials/', blank=True, null=True)
    
    # Tracking
    notion_id = models.CharField(max_length=36, blank=True, help_text="Notion database ID")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-start_time']
        verbose_name = 'Chapter Activity'
        verbose_name_plural = 'Chapter Activities'
    
    def __str__(self):
        return f"{self.title} - {self.chapter.name} ({self.date})"
    
    def get_absolute_url(self):
        return reverse('activity_detail', args=[self.pk])


class ActivityAttendance(models.Model):
    """
    Attendance tracking for chapter activities.
    """
    ATTENDANCE_STATUS = (
        ('registered', 'Registered'),
        ('attended', 'Attended'),
        ('absent', 'Absent'),
        ('cancelled', 'Cancelled'),
    )
    
    activity = models.ForeignKey(
        ChapterActivity,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    attendee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default='registered')
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    
    # For volunteer activities
    volunteer_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tasks_completed = models.TextField(blank=True)
    
    # Feedback
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    # Metadata
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('activity', 'attendee')
        ordering = ['activity', 'attendee']
    
    def __str__(self):
        return f"{self.attendee.get_full_name()} - {self.activity.title}"