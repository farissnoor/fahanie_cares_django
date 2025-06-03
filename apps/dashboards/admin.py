from django.contrib import admin
from .models import Report, ScheduledReport, Dashboard, DashboardWidget


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'created_by', 'created_at', 'format']
    list_filter = ['report_type', 'format', 'created_at']
    search_fields = ['name', 'created_by__email']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'report_type', 'format')
        }),
        ('Parameters', {
            'fields': ('parameters', 'file_path'),
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'is_scheduled'),
        }),
    )


@admin.register(ScheduledReport)
class ScheduledReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'frequency', 'is_active', 'next_run']
    list_filter = ['report_type', 'frequency', 'is_active']
    search_fields = ['name', 'created_by__email']
    readonly_fields = ['id', 'created_at', 'last_run']
    filter_horizontal = ['recipients']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'report_type', 'frequency', 'is_active')
        }),
        ('Schedule', {
            'fields': ('next_run', 'last_run'),
        }),
        ('Configuration', {
            'fields': ('parameters', 'recipients'),
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
        }),
    )


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['name', 'dashboard_type', 'created_by', 'is_public', 'created_at']
    list_filter = ['dashboard_type', 'is_public', 'created_at']
    search_fields = ['name', 'created_by__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'dashboard_type', 'is_public')
        }),
        ('Configuration', {
            'fields': ('config',),
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
        }),
    )


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ['title', 'dashboard', 'widget_type', 'data_source', 'position']
    list_filter = ['widget_type', 'chart_type', 'data_source']
    search_fields = ['title', 'dashboard__name']
    ordering = ['dashboard', 'position']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'dashboard', 'title', 'widget_type', 'chart_type')
        }),
        ('Data Configuration', {
            'fields': ('data_source', 'filters'),
        }),
        ('Layout', {
            'fields': ('position', 'width', 'height'),
        }),
        ('Advanced', {
            'fields': ('config',),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('dashboard')