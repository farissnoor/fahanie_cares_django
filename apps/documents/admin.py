from django.contrib import admin
from .models import DocumentCategory, Document, DocumentAccess, DocumentTemplate


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'description')
    list_filter = ('parent',)
    search_fields = ('name', 'description')
    ordering = ('parent', 'name')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'file_type', 'status', 'version', 'uploaded_by', 'created_at')
    list_filter = ('status', 'category', 'file_type', 'is_public', 'created_at')
    search_fields = ('title', 'description', 'tags')
    readonly_fields = ('id', 'file_size', 'file_type', 'version', 'created_at', 'updated_at', 'notion_id')
    date_hierarchy = 'created_at'
    raw_id_fields = ('constituent', 'referral', 'uploaded_by', 'parent_document')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'file', 'category', 'tags')
        }),
        ('Relationships', {
            'fields': ('constituent', 'referral', 'uploaded_by')
        }),
        ('Status', {
            'fields': ('status', 'is_public')
        }),
        ('Version Control', {
            'fields': ('version', 'parent_document')
        }),
        ('System Information', {
            'fields': ('id', 'file_size', 'file_type', 'created_at', 'updated_at', 'notion_id'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category', 'uploaded_by', 'constituent', 'referral')


@admin.register(DocumentAccess)
class DocumentAccessAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'action', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('document__title', 'user__username', 'user__email')
    readonly_fields = ('document', 'user', 'action', 'timestamp', 'ip_address')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        # Don't allow manual creation of access logs
        return False
    
    def has_change_permission(self, request, obj=None):
        # Don't allow editing of access logs
        return False


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'description', 'category', 'file')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )