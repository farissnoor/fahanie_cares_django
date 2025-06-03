"""
Enhanced notification service with support for multiple channels.
"""
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from .models import (
    Notification, NotificationChannel, NotificationType,
    NotificationPreference, NotificationTemplate, NotificationLog,
    NotificationQueue
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Enhanced notification service."""
    
    def __init__(self):
        self.email_sender = EmailNotificationSender()
        self.push_sender = PushNotificationSender()
        self.sms_sender = SMSNotificationSender()
    
    def send_notification(
        self,
        user,
        notification_type: NotificationType,
        title: str,
        message: str,
        related_object=None,
        data: Optional[Dict] = None,
        priority: str = 'normal',
        channels: Optional[List[NotificationChannel]] = None,
        template_name: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Notification:
        """
        Send a notification through multiple channels.
        
        Args:
            user: User to receive the notification
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            related_object: Related Django model instance
            data: Additional data to store with notification
            priority: Notification priority
            channels: Specific channels to use (None = use user preferences)
            template_name: Template to use (for template-based notifications)
            context: Context for template rendering
            
        Returns:
            Notification instance
        """
        # Get user preferences
        try:
            preferences = user.notification_preferences
        except NotificationPreference.DoesNotExist:
            preferences = NotificationPreference.objects.create(user=user)
        
        # Check if notification type is enabled
        if not preferences.is_type_enabled(notification_type):
            logger.info(f"Notification type {notification_type} disabled for user {user.id}")
            return None
        
        # Determine channels to use
        if channels is None:
            channels = self._get_enabled_channels(preferences)
        
        # Create notification instance
        notification = Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            priority=priority,
            data=data or {},
        )
        
        # Set related object if provided
        if related_object:
            notification.content_type = ContentType.objects.get_for_model(related_object)
            notification.object_id = str(related_object.pk)
            notification.save()
        
        # Send through each channel
        for channel in channels:
            try:
                self._send_through_channel(notification, channel, template_name, context)
                notification.channels_attempted.append(channel.value)
            except Exception as e:
                logger.error(f"Failed to send notification {notification.id} through {channel}: {str(e)}")
                self._log_failure(notification, channel, str(e))
        
        notification.save()
        return notification
    
    def _get_enabled_channels(self, preferences: NotificationPreference) -> List[NotificationChannel]:
        """Get list of enabled channels for user."""
        channels = []
        
        if preferences.email_enabled:
            channels.append(NotificationChannel.EMAIL)
        if preferences.in_app_enabled:
            channels.append(NotificationChannel.IN_APP)
        if preferences.push_enabled:
            channels.append(NotificationChannel.PUSH)
        if preferences.sms_enabled:
            channels.append(NotificationChannel.SMS)
        
        return channels
    
    def _send_through_channel(
        self,
        notification: Notification,
        channel: NotificationChannel,
        template_name: Optional[str] = None,
        context: Optional[Dict] = None
    ):
        """Send notification through specific channel."""
        if channel == NotificationChannel.EMAIL:
            success = self.email_sender.send(notification, template_name, context)
        elif channel == NotificationChannel.PUSH:
            success = self.push_sender.send(notification)
        elif channel == NotificationChannel.SMS:
            success = self.sms_sender.send(notification)
        elif channel == NotificationChannel.IN_APP:
            # In-app notifications are already created, just mark as delivered
            success = True
        else:
            success = False
        
        if success:
            notification.mark_delivered(channel)
            self._log_success(notification, channel)
        else:
            self._log_failure(notification, channel, "Send failed")
    
    def _log_success(self, notification: Notification, channel: NotificationChannel):
        """Log successful notification delivery."""
        NotificationLog.objects.create(
            notification=notification,
            channel=channel.value,
            status='delivered',
            delivered_at=timezone.now()
        )
    
    def _log_failure(self, notification: Notification, channel: NotificationChannel, error: str):
        """Log failed notification delivery."""
        NotificationLog.objects.create(
            notification=notification,
            channel=channel.value,
            status='failed',
            error_message=error,
            failed_at=timezone.now()
        )
    
    def queue_notification(
        self,
        notification: Notification,
        channel: NotificationChannel,
        scheduled_for=None,
        priority: int = 0
    ) -> NotificationQueue:
        """Queue a notification for later delivery."""
        return NotificationQueue.objects.create(
            notification=notification,
            channel=channel.value,
            scheduled_for=scheduled_for or timezone.now(),
            priority=priority
        )
    
    def process_queue(self, channel: Optional[NotificationChannel] = None):
        """Process queued notifications."""
        queue_items = NotificationQueue.objects.filter(
            is_processed=False,
            scheduled_for__lte=timezone.now()
        )
        
        if channel:
            queue_items = queue_items.filter(channel=channel.value)
        
        queue_items = queue_items.order_by('-priority', 'scheduled_for')
        
        for item in queue_items:
            try:
                self._send_through_channel(
                    item.notification,
                    NotificationChannel(item.channel)
                )
                item.is_processed = True
                item.processed_at = timezone.now()
                item.save()
            except Exception as e:
                logger.error(f"Failed to process queue item {item.id}: {str(e)}")
                item.retry_count += 1
                item.last_error = str(e)
                
                if item.retry_count >= item.max_retries:
                    item.is_processed = True
                    item.processed_at = timezone.now()
                
                item.save()


class EmailNotificationSender:
    """Email notification sender."""
    
    def send(
        self,
        notification: Notification,
        template_name: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> bool:
        """Send email notification."""
        user = notification.user
        
        if not user.email:
            logger.warning(f"Cannot send email to user {user.id} - no email address")
            return False
        
        try:
            # Prepare context
            email_context = {
                'user': user,
                'notification': notification,
                'site_name': getattr(settings, 'SITE_NAME', '#FahanieCares'),
                'site_url': getattr(settings, 'SITE_URL', 'https://fahanie-cares.gov.ph'),
            }
            
            if context:
                email_context.update(context)
            
            # Determine template
            if template_name:
                html_template = f'emails/{template_name}.html'
                text_template = f'emails/{template_name}.txt'
            else:
                html_template = f'emails/notifications/{notification.type}.html'
                text_template = f'emails/notifications/{notification.type}.txt'
            
            # Render content
            try:
                html_content = render_to_string(html_template, email_context)
            except Exception:
                # Fallback to generic template
                html_content = render_to_string('emails/generic_notification.html', email_context)
            
            text_content = strip_tags(html_content)
            
            # Send email
            msg = EmailMultiAlternatives(
                notification.title,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Sent email notification {notification.id} to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification {notification.id}: {str(e)}")
            return False


class PushNotificationSender:
    """Push notification sender (placeholder for implementation)."""
    
    def send(self, notification: Notification) -> bool:
        """Send push notification."""
        # TODO: Implement push notification service (FCM, OneSignal, etc.)
        logger.info(f"Push notification {notification.id} queued for delivery")
        return True


class SMSNotificationSender:
    """SMS notification sender (placeholder for implementation)."""
    
    def send(self, notification: Notification) -> bool:
        """Send SMS notification."""
        # TODO: Implement SMS service (Twilio, etc.)
        logger.info(f"SMS notification {notification.id} queued for delivery")
        return False


# Convenience functions
def send_notification(
    user,
    notification_type: NotificationType,
    title: str,
    message: str,
    **kwargs
) -> Notification:
    """Send a notification."""
    service = NotificationService()
    return service.send_notification(user, notification_type, title, message, **kwargs)


def send_bulk_notification(
    users,
    notification_type: NotificationType,
    title: str,
    message: str,
    **kwargs
) -> List[Notification]:
    """Send notification to multiple users."""
    service = NotificationService()
    notifications = []
    
    for user in users:
        notification = service.send_notification(user, notification_type, title, message, **kwargs)
        if notification:
            notifications.append(notification)
    
    return notifications