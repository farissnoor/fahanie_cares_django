import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class NotificationChannel(models.TextChoices):
    """Notification delivery channels."""
    EMAIL = 'email', 'Email'
    IN_APP = 'in_app', 'In-App'
    PUSH = 'push', 'Push Notification'
    SMS = 'sms', 'SMS'


class NotificationType(models.TextChoices):
    """Types of notifications."""
    REFERRAL_STATUS = 'referral_status', 'Referral Status Update'
    REFERRAL_COMMENT = 'referral_comment', 'Referral Comment'
    DOCUMENT_UPLOAD = 'document_upload', 'Document Upload'
    DOCUMENT_STATUS = 'document_status', 'Document Status Update'
    CHAPTER_EVENT = 'chapter_event', 'Chapter Event'
    SERVICE_UPDATE = 'service_update', 'Service Update'
    SYSTEM_ANNOUNCEMENT = 'system_announcement', 'System Announcement'
    ACCOUNT_UPDATE = 'account_update', 'Account Update'


class NotificationPreference(models.Model):
    """User preferences for notifications."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Channel preferences
    email_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    
    # Type preferences (JSON field for flexibility)
    enabled_types = models.JSONField(default=dict, help_text="Dictionary of notification types and their enabled status")
    
    # Frequency preferences
    digest_frequency = models.CharField(max_length=20, choices=[
        ('immediate', 'Immediate'),
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ], default='immediate')
    
    # Quiet hours
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='Asia/Manila')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification preferences for {self.user}"
    
    def is_channel_enabled(self, channel: NotificationChannel) -> bool:
        """Check if a notification channel is enabled."""
        if channel == NotificationChannel.EMAIL:
            return self.email_enabled
        elif channel == NotificationChannel.IN_APP:
            return self.in_app_enabled
        elif channel == NotificationChannel.PUSH:
            return self.push_enabled
        elif channel == NotificationChannel.SMS:
            return self.sms_enabled
        return False
    
    def is_type_enabled(self, notification_type: NotificationType) -> bool:
        """Check if a notification type is enabled."""
        return self.enabled_types.get(notification_type, True)  # Default to enabled
    
    def set_type_preference(self, notification_type: NotificationType, enabled: bool):
        """Set preference for a notification type."""
        if not self.enabled_types:
            self.enabled_types = {}
        self.enabled_types[notification_type] = enabled
        self.save()


class Notification(models.Model):
    """Notification model for tracking sent notifications."""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification details
    type = models.CharField(max_length=50, choices=NotificationType.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Related object (optional)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Metadata
    data = models.JSONField(default=dict, blank=True)
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery tracking
    channels_attempted = models.JSONField(default=list)
    channels_delivered = models.JSONField(default=list)
    email_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.type} notification for {self.user} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def mark_delivered(self, channel: NotificationChannel):
        """Mark notification as delivered through a channel."""
        if channel not in self.channels_delivered:
            self.channels_delivered.append(channel)
            
        if channel == NotificationChannel.EMAIL:
            self.email_sent = True
        elif channel == NotificationChannel.PUSH:
            self.push_sent = True
        elif channel == NotificationChannel.SMS:
            self.sms_sent = True
            
        self.save()
    
    @property
    def is_expired(self):
        """Check if notification has expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class NotificationTemplate(models.Model):
    """Templates for notifications."""
    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=50, choices=NotificationType.choices)
    
    # Template content
    subject_template = models.CharField(max_length=255, help_text="Subject template with variables like {user.name}")
    body_template = models.TextField(help_text="Body template with variables")
    html_template = models.TextField(blank=True, help_text="HTML template for emails")
    
    # Channel-specific templates
    push_title_template = models.CharField(max_length=100, blank=True)
    push_body_template = models.CharField(max_length=255, blank=True)
    sms_template = models.CharField(max_length=160, blank=True)
    
    # Metadata
    variables = models.JSONField(default=list, help_text="List of available template variables")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['type', 'name']
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.name}"


class NotificationLog(models.Model):
    """Log of all notification attempts."""
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Details
    metadata = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_channel_display()} log for {self.notification.title}"


class NotificationQueue(models.Model):
    """Queue for batch/delayed notifications."""
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='queue_items')
    channel = models.CharField(max_length=20, choices=NotificationChannel.choices)
    
    # Queue settings
    priority = models.IntegerField(default=0, help_text="Higher numbers = higher priority")
    scheduled_for = models.DateTimeField(default=timezone.now)
    
    # Status
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    last_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['priority', 'scheduled_for']
        indexes = [
            models.Index(fields=['is_processed', 'scheduled_for']),
            models.Index(fields=['channel', 'is_processed']),
        ]
    
    def __str__(self):
        return f"Queue item for {self.notification.title} via {self.get_channel_display()}"