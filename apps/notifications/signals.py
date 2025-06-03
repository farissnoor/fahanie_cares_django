"""
Signal handlers for automatic notifications.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from apps.referrals.models import Referral, ReferralUpdate
from apps.documents.models import Document
from .models import NotificationType
from .services import send_notification

User = get_user_model()


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create notification preferences for new users."""
    if created:
        from .models import NotificationPreference
        NotificationPreference.objects.create(user=instance)


@receiver(pre_save, sender=Referral)
def track_referral_status_change(sender, instance, **kwargs):
    """Track status changes for notifications."""
    if instance.pk:
        try:
            old_instance = Referral.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                instance._status_changed = True
                instance._old_status = old_instance.status
        except Referral.DoesNotExist:
            pass


@receiver(post_save, sender=Referral)
def send_referral_status_notification(sender, instance, created, **kwargs):
    """Send notification when referral status changes."""
    if not created and hasattr(instance, '_status_changed'):
        send_notification(
            user=instance.constituent,
            notification_type=NotificationType.REFERRAL_STATUS,
            title=f"Referral {instance.reference_number} Status Updated",
            message=f"Your referral status has changed from {instance._old_status} to {instance.status}.",
            related_object=instance,
            data={
                'referral_id': str(instance.id),
                'reference_number': instance.reference_number,
                'old_status': instance._old_status,
                'new_status': instance.status,
                'url': f'/referrals/{instance.id}/',
            }
        )


@receiver(post_save, sender=ReferralUpdate)
def send_referral_comment_notification(sender, instance, created, **kwargs):
    """Send notification for new referral comments."""
    if created and instance.update_type == 'comment':
        referral = instance.referral
        user = referral.constituent
        
        # Don't notify about user's own comments
        if instance.created_by != user:
            send_notification(
                user=user,
                notification_type=NotificationType.REFERRAL_COMMENT,
                title=f"New Comment on Referral {referral.reference_number}",
                message=f"{instance.created_by.get_full_name()} commented: {instance.notes[:100]}...",
                related_object=instance,
                data={
                    'referral_id': str(referral.id),
                    'update_id': str(instance.id),
                    'commenter': instance.created_by.get_full_name(),
                    'url': f'/referrals/{referral.id}/#update-{instance.id}',
                }
            )


@receiver(post_save, sender=Document)
def send_document_notification(sender, instance, created, **kwargs):
    """Send notification for document uploads."""
    if created:
        # Notify related constituent
        if instance.constituent and instance.uploaded_by != instance.constituent:
            send_notification(
                user=instance.constituent,
                notification_type=NotificationType.DOCUMENT_UPLOAD,
                title=f"New Document Uploaded: {instance.title}",
                message=f"A new document has been uploaded to your profile by {instance.uploaded_by.get_full_name()}.",
                related_object=instance,
                data={
                    'document_id': str(instance.id),
                    'document_title': instance.title,
                    'uploader': instance.uploaded_by.get_full_name(),
                    'url': f'/documents/{instance.id}/',
                }
            )
        
        # Notify related referral constituent
        if instance.referral and instance.uploaded_by != instance.referral.constituent:
            send_notification(
                user=instance.referral.constituent,
                notification_type=NotificationType.DOCUMENT_UPLOAD,
                title=f"New Document for Referral {instance.referral.reference_number}",
                message=f"A document has been uploaded to your referral: {instance.title}",
                related_object=instance,
                data={
                    'document_id': str(instance.id),
                    'referral_id': str(instance.referral.id),
                    'document_title': instance.title,
                    'url': f'/referrals/{instance.referral.id}/documents/{instance.id}/',
                }
            )


@receiver(pre_save, sender=Document)
def track_document_status_change(sender, instance, **kwargs):
    """Track document status changes."""
    if instance.pk:
        try:
            old_instance = Document.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                instance._status_changed = True
                instance._old_status = old_instance.status
        except Document.DoesNotExist:
            pass


@receiver(post_save, sender=Document)
def send_document_status_notification(sender, instance, created, **kwargs):
    """Send notification when document status changes."""
    if not created and hasattr(instance, '_status_changed'):
        # Notify uploader
        if instance.uploaded_by:
            send_notification(
                user=instance.uploaded_by,
                notification_type=NotificationType.DOCUMENT_STATUS,
                title=f"Document {instance.title} Status Updated",
                message=f"Your document status has changed from {instance._old_status} to {instance.status}.",
                related_object=instance,
                data={
                    'document_id': str(instance.id),
                    'document_title': instance.title,
                    'old_status': instance._old_status,
                    'new_status': instance.status,
                    'url': f'/documents/{instance.id}/',
                }
            )