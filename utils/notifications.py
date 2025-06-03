"""
Notification system for #FahanieCares.
Manages sending notifications to users about various events in the system.
"""

import logging
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service for sending notifications to users.
    """
    
    @staticmethod
    def send_referral_status_notification(referral, update=None):
        """
        Send a notification about a referral status change.
        
        Args:
            referral: The Referral instance
            update: Optional ReferralUpdate instance with details about the change
        """
        user = referral.constituent
        if not user.email:
            logger.warning(f"Cannot send email notification to user {user.id} - no email address")
            return False
            
        try:
            # Prepare context for the template
            context = {
                'user': user,
                'referral': referral,
                'update': update,
                'site_name': getattr(settings, 'SITE_NAME', '#FahanieCares'),
                'site_url': getattr(settings, 'SITE_URL', 'https://fahanie-cares.gov.ph'),
            }
            
            # Render the email content
            html_content = render_to_string('emails/referral_status_update.html', context)
            text_content = strip_tags(html_content)
            
            # Create the email subject based on the status
            status_display = referral.get_status_display()
            subject = f"Your Service Referral ({referral.reference_number}) is now {status_display}"
            
            # Send the email
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Sent referral status notification email to {user.email} for referral {referral.reference_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send referral status notification: {str(e)}")
            return False
    
    @staticmethod
    def send_referral_comment_notification(referral, update):
        """
        Send a notification about a new comment on a referral.
        
        Args:
            referral: The Referral instance
            update: The ReferralUpdate instance with the comment
        """
        user = referral.constituent
        if not user.email:
            logger.warning(f"Cannot send email notification to user {user.id} - no email address")
            return False
            
        # Don't notify about user's own comments
        if update.created_by == user:
            logger.debug(f"Skipping notification for user's own comment on referral {referral.reference_number}")
            return False
            
        try:
            # Prepare context for the template
            context = {
                'user': user,
                'referral': referral,
                'update': update,
                'commenter': update.created_by,
                'site_name': getattr(settings, 'SITE_NAME', '#FahanieCares'),
                'site_url': getattr(settings, 'SITE_URL', 'https://fahanie-cares.gov.ph'),
            }
            
            # Render the email content
            html_content = render_to_string('emails/referral_comment.html', context)
            text_content = strip_tags(html_content)
            
            # Create the email subject
            subject = f"New update on your Service Referral ({referral.reference_number})"
            
            # Send the email
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Sent referral comment notification email to {user.email} for referral {referral.reference_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send referral comment notification: {str(e)}")
            return False
    
    @staticmethod
    def send_document_upload_notification(document):
        """
        Send a notification about a document being uploaded to a referral.
        
        Args:
            document: The ReferralDocument instance
        """
        referral = document.referral
        user = referral.constituent
        
        if not user.email:
            logger.warning(f"Cannot send email notification to user {user.id} - no email address")
            return False
            
        # Don't notify about user's own uploads
        if document.uploaded_by == user:
            logger.debug(f"Skipping notification for user's own document upload on referral {referral.reference_number}")
            return False
            
        try:
            # Prepare context for the template
            context = {
                'user': user,
                'referral': referral,
                'document': document,
                'uploader': document.uploaded_by,
                'site_name': getattr(settings, 'SITE_NAME', '#FahanieCares'),
                'site_url': getattr(settings, 'SITE_URL', 'https://fahanie-cares.gov.ph'),
            }
            
            # Render the email content
            html_content = render_to_string('emails/document_upload.html', context)
            text_content = strip_tags(html_content)
            
            # Create the email subject
            subject = f"New document added to your Service Referral ({referral.reference_number})"
            
            # Send the email
            msg = EmailMultiAlternatives(
                subject,
                text_content,
                settings.DEFAULT_FROM_EMAIL,
                [user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Sent document upload notification email to {user.email} for referral {referral.reference_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send document upload notification: {str(e)}")
            return False

# Create a simple function for compatibility
def send_notification(user, subject, message, notification_type='info', **kwargs):
    """
    Send a notification to a user.
    
    Args:
        user: The user to send the notification to
        subject: Subject of the notification
        message: Message body
        notification_type: Type of notification (info, success, warning, error)
        **kwargs: Additional context for the notification
    """
    from apps.notifications.models import Notification
    
    try:
        # Create an in-app notification
        notification = Notification.objects.create(
            user=user,
            subject=subject,
            message=message,
            notification_type=notification_type,
            metadata=kwargs
        )
        
        # If email is required, send it
        if kwargs.get('send_email', True) and user.email:
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Failed to send email notification: {str(e)}")
        
        return notification
        
    except Exception as e:
        logger.error(f"Failed to create notification: {str(e)}")
        return None