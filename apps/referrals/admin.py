from django.contrib import admin
from django.utils import timezone
from .models import Agency, ServiceCategory, Service, Referral, ReferralUpdate, ReferralDocument

@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'ministry', 'contact_person', 'is_active')
    list_filter = ('is_active', 'ministry')
    search_fields = ('name', 'abbreviation', 'ministry', 'contact_person')
    ordering = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name', 'abbreviation', 'ministry', 'description', 'logo')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_email', 'contact_phone', 'address', 'website')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Notion Integration', {
            'fields': ('notion_id',),
            'classes': ('collapse',)
        }),
    )

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'order', 'slug')
    list_filter = ('parent',)
    search_fields = ('name', 'description')
    ordering = ('order', 'name')
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'icon', 'slug', 'parent', 'order')
        }),
        ('Notion Integration', {
            'fields': ('notion_id',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'agency', 'is_active')
    list_filter = ('is_active', 'category', 'agency')
    search_fields = ('name', 'description', 'category__name', 'agency__name')
    ordering = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'category', 'agency', 'slug')
        }),
        ('Service Details', {
            'fields': ('eligibility_criteria', 'required_documents', 'application_process', 'processing_time', 'fees')
        }),
        ('Contact and Links', {
            'fields': ('contact_info', 'website_link', 'form_link')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Notion Integration', {
            'fields': ('notion_id',),
            'classes': ('collapse',)
        }),
    )

class ReferralUpdateInline(admin.TabularInline):
    model = ReferralUpdate
    extra = 1
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('status', 'notes', 'created_by', 'created_at')
        }),
    )

class ReferralDocumentInline(admin.TabularInline):
    model = ReferralDocument
    extra = 1
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('name', 'file', 'uploaded_by', 'created_at')
        }),
    )

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'constituent', 'service', 'status', 'priority', 'submitted_at', 'assigned_to')
    list_filter = ('status', 'priority', 'service__category')
    search_fields = ('reference_number', 'constituent__username', 'constituent__first_name', 'constituent__last_name', 'description')
    readonly_fields = ('reference_number', 'submitted_at', 'referred_at', 'completed_at', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    inlines = [ReferralUpdateInline, ReferralDocumentInline]
    fieldsets = (
        (None, {
            'fields': ('reference_number', 'constituent', 'service', 'status', 'priority')
        }),
        ('Request Details', {
            'fields': ('description', 'supporting_documents')
        }),
        ('Staff Information', {
            'fields': ('assigned_to', 'staff_notes', 'follow_up_date')
        }),
        ('Agency Information', {
            'fields': ('agency_contact', 'agency_reference', 'agency_notes')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'referred_at', 'completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Notion Integration', {
            'fields': ('notion_id',),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_as_submitted', 'mark_as_processing', 'mark_as_completed']
    
    def mark_as_submitted(self, request, queryset):
        updated = queryset.update(status='submitted', submitted_at=timezone.now())
        self.message_user(request, f"{updated} referrals marked as submitted.")
    mark_as_submitted.short_description = "Mark selected referrals as submitted"
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f"{updated} referrals marked as processing.")
    mark_as_processing.short_description = "Mark selected referrals as processing"
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f"{updated} referrals marked as completed.")
    mark_as_completed.short_description = "Mark selected referrals as completed"
