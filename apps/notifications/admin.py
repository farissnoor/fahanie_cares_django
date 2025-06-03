from django.contrib import admin
from .models import (
    NotificationPreference, Notification, NotificationTemplate,
    NotificationLog, NotificationQueue
)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_enabled', 'in_app_enabled', 'push_enabled', 'sms_enabled', 'digest_frequency')
    list_filter = ('email_enabled', 'in_app_enabled', 'push_enabled', 'sms_enabled', 'digest_frequency')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'type', 'priority', 'is_read', 'created_at')
    list_filter = ('type', 'priority', 'is_read', 'email_sent', 'push_sent', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'user__email')
    readonly_fields = ('id', 'created_at', 'read_at', 'channels_attempted', 'channels_delivered')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'type', 'title', 'message', 'priority')
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'expires_at')
        }),
        ('Delivery', {
            'fields': ('channels_attempted', 'channels_delivered', 'email_sent', 'push_sent', 'sms_sent')
        }),
        ('Metadata', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('System', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'is_active', 'created_at')
    list_filter = ('type', 'is_active')
    search_fields = ('name', 'subject_template', 'body_template')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'type', 'is_active')
        }),
        ('Email Templates', {
            'fields': ('subject_template', 'body_template', 'html_template')
        }),
        ('Push Notification Templates', {
            'fields': ('push_title_template', 'push_body_template'),
            'classes': ('collapse',)
        }),
        ('SMS Template', {
            'fields': ('sms_template',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('variables', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('notification', 'channel', 'status', 'created_at')
    list_filter = ('channel', 'status', 'created_at')
    search_fields = ('notification__title', 'error_message')
    readonly_fields = ('notification', 'channel', 'status', 'created_at', 'sent_at', 'delivered_at', 'failed_at')
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(NotificationQueue)
class NotificationQueueAdmin(admin.ModelAdmin):
    list_display = ('notification', 'channel', 'priority', 'scheduled_for', 'is_processed', 'created_at')
    list_filter = ('channel', 'is_processed', 'scheduled_for')
    search_fields = ('notification__title',)
    readonly_fields = ('created_at', 'processed_at')
    date_hierarchy = 'scheduled_for'
    
    actions = ['process_queue_items']
    
    def process_queue_items(self, request, queryset):
        """Process selected queue items."""
        from .services import NotificationService
        service = NotificationService()
        count = 0
        
        for item in queryset.filter(is_processed=False):
            try:
                service._send_through_channel(
                    item.notification,
                    NotificationChannel(item.channel)
                )
                item.is_processed = True
                item.processed_at = timezone.now()
                item.save()
                count += 1
            except Exception as e:
                self.message_user(request, f"Error processing {item}: {str(e)}", level=messages.ERROR)
        
        self.message_user(request, f"Successfully processed {count} notification(s).")
    
    process_queue_items.short_description = "Process selected queue items"