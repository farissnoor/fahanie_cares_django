from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    ContactFormSubmission, CommunicationTemplate, CommunicationCampaign,
    CommunicationMessage, AnnouncementPost, CommunicationSettings
)


@admin.register(ContactFormSubmission)
class ContactFormSubmissionAdmin(admin.ModelAdmin):
    """
    Admin interface for managing contact form submissions.
    """
    list_display = [
        'get_full_name', 'email', 'subject_display', 'form_source', 
        'status', 'submitted_at', 'is_recent_indicator'
    ]
    list_filter = [
        'status', 'subject', 'form_source', 'submitted_at', 'assigned_to'
    ]
    search_fields = [
        'first_name', 'last_name', 'email', 'message'
    ]
    readonly_fields = [
        'submitted_at', 'updated_at', 'get_full_name'
    ]
    fieldsets = (
        ('Contact Information', {
            'fields': ('first_name', 'middle_name', 'last_name', 'email', 'phone_number')
        }),
        ('Message Details', {
            'fields': ('subject', 'message', 'form_source')
        }),
        ('Status & Assignment', {
            'fields': ('status', 'assigned_to', 'internal_notes')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_in_progress', 'mark_as_resolved', 'mark_as_closed']
    
    def get_full_name(self, obj):
        """Display full name in admin."""
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'first_name'
    
    def subject_display(self, obj):
        """Display subject with color coding."""
        colors = {
            'assistance': '#dc2626',  # red
            'feedback': '#2563eb',    # blue
            'volunteer': '#16a34a',   # green
            'chapter': '#7c3aed',     # purple
            'other': '#6b7280',       # gray
        }
        color = colors.get(obj.subject, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_subject_display()
        )
    subject_display.short_description = 'Subject'
    subject_display.admin_order_field = 'subject'
    
    def is_recent_indicator(self, obj):
        """Show if submission is recent."""
        if obj.is_recent:
            return format_html('<span style="color: #16a34a;">🆕 Recent</span>')
        return ''
    is_recent_indicator.short_description = 'Recent'
    
    def mark_as_in_progress(self, request, queryset):
        """Mark selected submissions as in progress."""
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} submission(s) marked as in progress.')
    mark_as_in_progress.short_description = 'Mark as In Progress'
    
    def mark_as_resolved(self, request, queryset):
        """Mark selected submissions as resolved."""
        updated = queryset.update(status='resolved')
        self.message_user(request, f'{updated} submission(s) marked as resolved.')
    mark_as_resolved.short_description = 'Mark as Resolved'
    
    def mark_as_closed(self, request, queryset):
        """Mark selected submissions as closed."""
        updated = queryset.update(status='closed')
        self.message_user(request, f'{updated} submission(s) marked as closed.')
    mark_as_closed.short_description = 'Mark as Closed'


# Register other models if they aren't already registered
try:
    admin.site.register(CommunicationTemplate)
except admin.sites.AlreadyRegistered:
    pass

try:
    admin.site.register(CommunicationCampaign)
except admin.sites.AlreadyRegistered:
    pass

try:
    admin.site.register(CommunicationMessage)
except admin.sites.AlreadyRegistered:
    pass

try:
    admin.site.register(AnnouncementPost)
except admin.sites.AlreadyRegistered:
    pass

try:
    admin.site.register(CommunicationSettings)
except admin.sites.AlreadyRegistered:
    pass