from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import EmailValidator
from apps.constituents.models import Constituent, ConstituentGroup
from apps.chapters.models import Chapter


class ContactFormSubmission(models.Model):
    """
    Stores contact form submissions from various forms across the site.
    """
    SUBJECT_CHOICES = (
        ('assistance', 'Request Assistance'),
        ('feedback', 'Provide Feedback'),
        ('volunteer', 'Volunteer Opportunities'),
        ('chapter', 'Chapter Inquiries'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    # Contact Information
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(validators=[EmailValidator()])
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Message Details
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    message = models.TextField()
    
    # Metadata
    form_source = models.CharField(max_length=50, help_text="Which page/form this submission came from")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional staff assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_contact_submissions'
    )
    
    # Internal notes
    internal_notes = models.TextField(blank=True, null=True, help_text="Internal notes for staff use")
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = "Contact Form Submission"
        verbose_name_plural = "Contact Form Submissions"
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.get_subject_display()} ({self.submitted_at.strftime('%Y-%m-%d')})"
    
    def get_full_name(self):
        """Return the full name of the contact."""
        names = [self.first_name]
        if self.middle_name:
            names.append(self.middle_name)
        names.append(self.last_name)
        return ' '.join(names)
    
    @property
    def is_recent(self):
        """Check if submission was made in the last 48 hours."""
        return (timezone.now() - self.submitted_at).days < 2


class PartnershipSubmission(models.Model):
    """
    Model for storing partnership inquiries and applications.
    """
    PARTNERSHIP_TYPES = (
        ('ngo', 'NGO/Non-Profit Organization'),
        ('business', 'Business/Corporate'),
        ('government', 'Government Agency'),
        ('academic', 'Academic Institution'),
        ('community', 'Community Organization'),
        ('individual', 'Individual Partner'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('new', 'New'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('on_hold', 'On Hold'),
    )
    
    # Contact Information
    organization_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Partnership Details
    partnership_type = models.CharField(max_length=20, choices=PARTNERSHIP_TYPES)
    proposed_collaboration = models.TextField(help_text="Describe the proposed collaboration or partnership")
    resources_offered = models.TextField(blank=True, null=True, help_text="What resources can you offer?")
    expected_outcomes = models.TextField(blank=True, null=True, help_text="What outcomes do you expect from this partnership?")
    
    # Administrative
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_partnerships'
    )
    notes = models.TextField(blank=True, null=True, help_text="Internal notes about this partnership")
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Partnership Submission'
        verbose_name_plural = 'Partnership Submissions'
    
    def __str__(self):
        return f"{self.organization_name} - {self.get_partnership_type_display()}"


class DonationSubmission(models.Model):
    """
    Model for storing donation inquiries and pledges.
    """
    DONATION_TYPES = (
        ('monetary', 'Monetary Donation'),
        ('goods', 'Goods/Materials'),
        ('services', 'Services'),
        ('volunteer_time', 'Volunteer Time'),
        ('equipment', 'Equipment'),
        ('other', 'Other'),
    )
    
    DONATION_FREQUENCIES = (
        ('one_time', 'One-time'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    )
    
    STATUS_CHOICES = (
        ('inquiry', 'Inquiry'),
        ('pledged', 'Pledged'),
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    # Donor Information
    donor_name = models.CharField(max_length=100)
    donor_type = models.CharField(max_length=20, choices=(
        ('individual', 'Individual'),
        ('organization', 'Organization'),
        ('business', 'Business'),
    ), default='individual')
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    # Donation Details
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="For monetary donations")
    description = models.TextField(help_text="Describe the donation or intended use")
    frequency = models.CharField(max_length=20, choices=DONATION_FREQUENCIES, default='one_time')
    preferred_program = models.CharField(max_length=200, blank=True, null=True, help_text="Specific program to support")
    
    # Administrative
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inquiry')
    submitted_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_donations'
    )
    receipt_issued = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True, help_text="Internal notes about this donation")
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Donation Submission'
        verbose_name_plural = 'Donation Submissions'
    
    def __str__(self):
        if self.amount:
            return f"{self.donor_name} - ₱{self.amount} ({self.get_donation_type_display()})"
        return f"{self.donor_name} - {self.get_donation_type_display()}"


class CommunicationTemplate(models.Model):
    """
    Reusable templates for communications.
    """
    TEMPLATE_TYPES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('letter', 'Letter'),
        ('social', 'Social Media'),
    )
    
    TEMPLATE_CATEGORIES = (
        ('announcement', 'Announcement'),
        ('invitation', 'Event Invitation'),
        ('newsletter', 'Newsletter'),
        ('update', 'Program Update'),
        ('reminder', 'Reminder'),
        ('thank_you', 'Thank You'),
        ('birthday', 'Birthday Greeting'),
        ('holiday', 'Holiday Greeting'),
        ('emergency', 'Emergency Alert'),
    )
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    category = models.CharField(max_length=20, choices=TEMPLATE_CATEGORIES)
    
    # Content
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"


class CommunicationCampaign(models.Model):
    """
    Communication campaigns for targeted messaging.
    """
    CAMPAIGN_STATUS = (
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
    )
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    template = models.ForeignKey(
        CommunicationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Targeting
    target_all_constituents = models.BooleanField(default=False)
    target_groups = models.ManyToManyField(
        ConstituentGroup,
        blank=True,
        related_name='campaigns'
    )
    target_chapters = models.ManyToManyField(
        Chapter,
        blank=True,
        related_name='campaigns'
    )
    target_user_types = models.JSONField(default=list, blank=True)
    custom_recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='campaign_custom_recipients'
    )
    
    # Content customization
    subject = models.CharField(max_length=200)
    content = models.TextField()
    attachments = models.FileField(upload_to='campaign_attachments/', blank=True, null=True)
    
    # Scheduling
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS, default='draft')
    scheduled_time = models.DateTimeField(null=True, blank=True)
    sent_time = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    total_recipients = models.PositiveIntegerField(default=0)
    successful_sends = models.PositiveIntegerField(default=0)
    failed_sends = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_campaigns'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_recipients(self):
        """Get all recipients for this campaign."""
        recipients = []
        
        if self.target_all_constituents:
            recipients.extend(settings.AUTH_USER_MODEL.objects.filter(
                is_active=True
            ))
        else:
            # Groups
            for group in self.target_groups.all():
                recipients.extend(group.members.filter(
                    user__is_active=True
                ).values_list('user', flat=True))
            
            # Chapters
            for chapter in self.target_chapters.all():
                recipients.extend(chapter.memberships.filter(
                    status='active',
                    user__is_active=True
                ).values_list('user', flat=True))
            
            # User types
            if self.target_user_types:
                recipients.extend(settings.AUTH_USER_MODEL.objects.filter(
                    user_type__in=self.target_user_types,
                    is_active=True
                ))
            
            # Custom recipients
            recipients.extend(self.custom_recipients.filter(is_active=True))
        
        # Remove duplicates
        return list(set(recipients))
    
    def send(self):
        """Send the campaign."""
        from .tasks import send_campaign_messages
        self.status = 'sending'
        self.save()
        
        # Async task to send messages
        send_campaign_messages.delay(self.id)


class CommunicationMessage(models.Model):
    """
    Individual messages sent to constituents.
    """
    MESSAGE_TYPES = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Message'),
    )
    
    MESSAGE_STATUS = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    )
    
    # Campaign association
    campaign = models.ForeignKey(
        CommunicationCampaign,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,
        blank=True
    )
    
    # Recipient
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    
    # Message details
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    subject = models.CharField(max_length=200, blank=True)
    content = models.TextField()
    
    # Delivery
    status = models.CharField(max_length=20, choices=MESSAGE_STATUS, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveSmallIntegerField(default=0)
    
    # Tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'created_at']),
            models.Index(fields=['campaign', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_message_type_display()} to {self.recipient.get_full_name()}"
    
    def mark_as_read(self):
        """Mark message as read."""
        if self.status in ['delivered', 'sent']:
            self.status = 'read'
            self.read_at = timezone.now()
            self.save()


class AnnouncementPost(models.Model):
    """
    Public announcements and news posts.
    """
    POST_STATUS = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    
    POST_CATEGORIES = (
        ('news', 'News'),
        ('event', 'Event'),
        ('update', 'Update'),
        ('alert', 'Alert'),
        ('achievement', 'Achievement'),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.CharField(max_length=20, choices=POST_CATEGORIES)
    
    # Content
    summary = models.TextField(help_text="Brief summary for listing pages")
    content = models.TextField()
    featured_image = models.ImageField(upload_to='announcements/', blank=True, null=True)
    
    # Publishing
    status = models.CharField(max_length=20, choices=POST_STATUS, default='draft')
    published_date = models.DateTimeField(null=True, blank=True)
    
    # Visibility
    is_featured = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    show_on_homepage = models.BooleanField(default=True)
    
    # Targeting
    target_all = models.BooleanField(default=True)
    target_chapters = models.ManyToManyField(
        Chapter,
        blank=True,
        related_name='announcements'
    )
    target_user_types = models.JSONField(default=list, blank=True)
    
    # Metadata
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='authored_announcements'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-published_date', '-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Set published date when publishing
        if self.status == 'published' and not self.published_date:
            self.published_date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('announcement_detail', args=[self.slug])


class EventNotification(models.Model):
    """
    Event-based notifications.
    """
    EVENT_TYPES = (
        ('referral_status', 'Referral Status Change'),
        ('application_status', 'Application Status Change'),
        ('chapter_activity', 'Chapter Activity'),
        ('program_update', 'Program Update'),
        ('system', 'System Notification'),
    )
    
    NOTIFICATION_CHANNELS = (
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App'),
    )
    
    # Event details
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    event_object_id = models.CharField(max_length=50)
    event_description = models.TextField()
    
    # Recipient
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_notifications'
    )
    
    # Notification settings
    channels = models.JSONField(default=list)
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} for {self.recipient.get_full_name()}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def send(self):
        """Send notification through specified channels."""
        from .tasks import send_notification_task
        
        for channel in self.channels:
            send_notification_task.delay(self.id, channel)
        
        self.is_sent = True
        self.sent_at = timezone.now()
        self.save()


class CommunicationSettings(models.Model):
    """
    User communication preferences.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='communication_settings'
    )
    
    # Channel preferences
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    
    # Frequency preferences
    allow_marketing = models.BooleanField(default=True)
    allow_newsletters = models.BooleanField(default=True)
    allow_event_invites = models.BooleanField(default=True)
    allow_program_updates = models.BooleanField(default=True)
    
    # Notification preferences by type
    referral_notifications = models.BooleanField(default=True)
    application_notifications = models.BooleanField(default=True)
    chapter_notifications = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    # Language preference
    preferred_language = models.CharField(max_length=10, default='en')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Communication settings for {self.user.get_full_name()}"