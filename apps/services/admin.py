from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import models
from django.forms import TextInput, Textarea
from .models import (
    ServiceProgram, ServiceApplication, ServiceDisbursement, ServiceImpact,
    MinistryProgram, MinistryProgramHistory
)

User = get_user_model()

@admin.register(ServiceProgram)
class ServiceProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'program_type', 'status', 'start_date', 'end_date', 'beneficiary_count']
    list_filter = ['status', 'program_type', 'start_date']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ServiceApplication)
class ServiceApplicationAdmin(admin.ModelAdmin):
    list_display = ['application_number', 'program', 'applicant', 'status', 'submitted_at']
    list_filter = ['status', 'priority_level', 'submitted_at']
    search_fields = ['application_number', 'applicant__first_name', 'applicant__last_name']
    date_hierarchy = 'submitted_at'

@admin.register(ServiceDisbursement)
class ServiceDisbursementAdmin(admin.ModelAdmin):
    list_display = ['application', 'amount', 'method', 'status', 'scheduled_date', 'actual_date']
    list_filter = ['status', 'method', 'scheduled_date']
    search_fields = ['application__application_number', 'reference_number']

@admin.register(ServiceImpact)
class ServiceImpactAdmin(admin.ModelAdmin):
    list_display = ['program', 'report_date', 'period_start', 'period_end', 'total_beneficiaries']
    list_filter = ['report_date', 'program']
    date_hierarchy = 'report_date'


class MinistryProgramHistoryInline(admin.TabularInline):
    """Inline display of program history for audit trail."""
    model = MinistryProgramHistory
    extra = 0
    readonly_fields = ('action_type', 'changed_fields', 'old_values', 'new_values', 
                       'reason', 'changed_by', 'changed_at', 'ip_address')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(MinistryProgram)
class MinistryProgramAdmin(admin.ModelAdmin):
    """
    Enhanced Django admin for Ministry Programs with full CRUD capabilities,
    role-based permissions, and comprehensive audit trails.
    """
    
    # Display configuration
    list_display = [
        'code', 'title_display', 'ministry_display', 'ppa_type_display', 
        'status_display', 'budget_display', 'progress_display', 'created_by', 'last_modified'
    ]
    
    list_filter = [
        'ministry', 'ppa_type', 'status', 'priority_level', 'funding_source',
        'is_public', 'is_featured', 'requires_approval', 'is_deleted',
        'created_at', 'start_date', 'end_date'
    ]
    
    search_fields = [
        'code', 'title', 'description', 'objectives', 'target_beneficiaries',
        'implementing_units', 'partner_agencies'
    ]
    
    readonly_fields = [
        'code', 'slug', 'created_at', 'updated_at', 'last_modified_by',
        'approved_at', 'approved_by', 'deleted_at', 'deleted_by',
        'budget_utilization_display', 'program_duration_display'
    ]
    
    prepopulated_fields = {'slug': ('ministry', 'title')}
    
    date_hierarchy = 'created_at'
    
    ordering = ['-created_at', 'ministry', 'title']
    
    # Fieldsets for organized form layout
    fieldsets = (
        ('Basic Information', {
            'fields': (
                ('code', 'slug'),
                'title',
                ('ministry', 'ppa_type'),
                ('priority_level', 'status'),
            )
        }),
        ('Program Details', {
            'fields': (
                'description',
                'objectives',
                'expected_outcomes',
                'key_performance_indicators',
            ),
            'classes': ('wide',)
        }),
        ('Target and Coverage', {
            'fields': (
                'target_beneficiaries',
                'geographic_coverage',
                'estimated_beneficiaries',
            )
        }),
        ('Implementation', {
            'fields': (
                'implementation_strategy',
                'implementing_units',
                'partner_agencies',
            )
        }),
        ('Financial Information', {
            'fields': (
                ('total_budget', 'allocated_budget', 'utilized_budget'),
                ('funding_source', 'funding_details'),
                'budget_utilization_display',
            )
        }),
        ('Timeline', {
            'fields': (
                ('start_date', 'end_date'),
                ('duration_months', 'program_duration_display'),
            )
        }),
        ('Management', {
            'fields': (
                ('created_by', 'ministry_liaison', 'program_manager'),
                'last_modified_by',
            )
        }),
        ('Access Control', {
            'fields': (
                ('is_public', 'is_featured'),
                'requires_approval',
            )
        }),
        ('Documentation', {
            'fields': (
                'program_document',
                'implementation_guidelines',
                'monitoring_framework',
            ),
            'classes': ('collapse',)
        }),
        ('Integration', {
            'fields': (
                'notion_database_id',
                'external_system_id',
            ),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': (
                ('created_at', 'updated_at'),
                ('approved_at', 'approved_by'),
                ('deleted_at', 'deleted_by'),
                'deletion_reason',
            ),
            'classes': ('collapse',)
        }),
    )
    
    # Inline models
    inlines = [MinistryProgramHistoryInline]
    
    # Custom form widget sizing
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '80'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80})},
    }
    
    # Actions
    actions = [
        'approve_programs', 'suspend_programs', 'activate_programs',
        'mark_completed', 'soft_delete_programs', 'restore_programs',
        'mark_as_featured', 'remove_featured', 'export_to_csv'
    ]
    
    def get_queryset(self, request):
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        # Filter based on user role
        if request.user.user_type == 'mp':
            return qs  # MP can see all programs
        elif request.user.user_type == 'staff':
            return qs  # Staff can see all programs
        elif request.user.user_type in ['coordinator', 'chapter_member']:
            # Show only programs they're associated with
            return qs.filter(
                models.Q(created_by=request.user) |
                models.Q(ministry_liaison=request.user) |
                models.Q(program_manager=request.user)
            )
        else:
            # Other users see only public programs
            return qs.filter(is_public=True, is_deleted=False)
    
    def has_change_permission(self, request, obj=None):
        """Check if user can modify the program."""
        if not obj:
            return super().has_change_permission(request)
        
        if request.user.is_superuser:
            return True
        
        return obj.can_edit(request.user)
    
    def has_delete_permission(self, request, obj=None):
        """Check if user can delete the program."""
        if not obj:
            return super().has_delete_permission(request)
        
        if request.user.is_superuser:
            return True
        
        return obj.can_delete(request.user)
    
    def save_model(self, request, obj, form, change):
        """Override save to add audit trail."""
        if not change:  # New object
            obj.created_by = request.user
        
        obj.last_modified_by = request.user
        
        # Track changes for audit
        if change and obj.pk:
            old_obj = MinistryProgram.objects.get(pk=obj.pk)
            changed_fields = []
            old_values = {}
            new_values = {}
            
            for field in obj._meta.fields:
                field_name = field.name
                if hasattr(old_obj, field_name) and hasattr(obj, field_name):
                    old_val = getattr(old_obj, field_name)
                    new_val = getattr(obj, field_name)
                    if old_val != new_val:
                        changed_fields.append(field_name)
                        old_values[field_name] = str(old_val) if old_val else ''
                        new_values[field_name] = str(new_val) if new_val else ''
            
            if changed_fields:
                # Create history record after saving
                super().save_model(request, obj, form, change)
                MinistryProgramHistory.objects.create(
                    program=obj,
                    action_type='update',
                    changed_fields=changed_fields,
                    old_values=old_values,
                    new_values=new_values,
                    changed_by=request.user,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                return
        
        super().save_model(request, obj, form, change)
        
        # Create history for new objects
        if not change:
            MinistryProgramHistory.objects.create(
                program=obj,
                action_type='create',
                changed_by=request.user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    # Custom display methods
    def title_display(self, obj):
        """Display title with truncation for long titles."""
        if len(obj.title) > 50:
            return f"{obj.title[:47]}..."
        return obj.title
    title_display.short_description = 'Title'
    
    def ministry_display(self, obj):
        """Display ministry with color coding."""
        colors = {
            'mssd': '#e3f2fd',
            'mafar': '#e8f5e8',
            'mtit': '#fff3e0',
        }
        color = colors.get(obj.ministry, '#f5f5f5')
        return format_html(
            '<span style="background-color: {}; padding: 2px 6px; border-radius: 3px;">{}</span>',
            color,
            obj.get_ministry_display()
        )
    ministry_display.short_description = 'Ministry'
    
    def ppa_type_display(self, obj):
        """Display PPA type with badges."""
        badges = {
            'program': 'success',
            'project': 'primary',
            'activity': 'secondary'
        }
        badge = badges.get(obj.ppa_type, 'light')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            badge,
            obj.get_ppa_type_display()
        )
    ppa_type_display.short_description = 'Type'
    
    def status_display(self, obj):
        """Display status with color indicators."""
        colors = {
            'draft': '#6c757d',
            'pending_approval': '#ffc107',
            'active': '#28a745',
            'suspended': '#dc3545',
            'completed': '#17a2b8',
            'cancelled': '#6c757d',
            'archived': '#343a40'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def budget_display(self, obj):
        """Display budget with formatting."""
        if obj.total_budget:
            return f"₱{obj.total_budget:,.2f}"
        return "Not specified"
    budget_display.short_description = 'Total Budget'
    
    def progress_display(self, obj):
        """Display implementation progress."""
        if obj.is_deleted:
            return format_html('<span style="color: red;">Deleted</span>')
        
        progress = obj.get_budget_utilization_percentage()
        if progress > 0:
            return f"{progress:.1f}% utilized"
        return "0% utilized"
    progress_display.short_description = 'Progress'
    
    def last_modified(self, obj):
        """Display last modification info."""
        if obj.last_modified_by:
            return f"{obj.updated_at.strftime('%Y-%m-%d')} by {obj.last_modified_by.get_full_name()}"
        return obj.updated_at.strftime('%Y-%m-%d')
    last_modified.short_description = 'Last Modified'
    
    def budget_utilization_display(self, obj):
        """Read-only budget utilization display."""
        return f"{obj.get_budget_utilization_percentage():.1f}%"
    budget_utilization_display.short_description = 'Budget Utilization'
    
    def program_duration_display(self, obj):
        """Read-only program duration display."""
        if obj.start_date and obj.end_date:
            delta = obj.end_date - obj.start_date
            return f"{delta.days} days"
        return "Not specified"
    program_duration_display.short_description = 'Duration'
    
    # Custom Actions
    def approve_programs(self, request, queryset):
        """Approve selected programs."""
        count = 0
        for program in queryset:
            if program.can_edit(request.user):
                program.approve(request.user)
                count += 1
        
        self.message_user(request, f"{count} programs approved successfully.")
    approve_programs.short_description = "Approve selected programs"
    
    def suspend_programs(self, request, queryset):
        """Suspend selected programs."""
        count = queryset.filter(status='active').update(
            status='suspended',
            last_modified_by=request.user
        )
        self.message_user(request, f"{count} programs suspended.")
    suspend_programs.short_description = "Suspend selected programs"
    
    def activate_programs(self, request, queryset):
        """Activate selected programs."""
        count = queryset.filter(status__in=['draft', 'suspended']).update(
            status='active',
            last_modified_by=request.user
        )
        self.message_user(request, f"{count} programs activated.")
    activate_programs.short_description = "Activate selected programs"
    
    def mark_completed(self, request, queryset):
        """Mark selected programs as completed."""
        count = queryset.filter(status='active').update(
            status='completed',
            last_modified_by=request.user
        )
        self.message_user(request, f"{count} programs marked as completed.")
    mark_completed.short_description = "Mark as completed"
    
    def soft_delete_programs(self, request, queryset):
        """Soft delete selected programs."""
        count = 0
        for program in queryset:
            if program.can_delete(request.user):
                program.soft_delete(request.user, "Bulk deletion via admin")
                count += 1
        
        self.message_user(request, f"{count} programs deleted.")
    soft_delete_programs.short_description = "Delete selected programs"
    
    def restore_programs(self, request, queryset):
        """Restore soft-deleted programs."""
        count = 0
        for program in queryset.filter(is_deleted=True):
            program.restore(request.user)
            count += 1
        
        self.message_user(request, f"{count} programs restored.")
    restore_programs.short_description = "Restore deleted programs"
    
    def mark_as_featured(self, request, queryset):
        """Mark selected programs as featured."""
        count = queryset.update(is_featured=True)
        self.message_user(request, f"{count} programs marked as featured.")
    mark_as_featured.short_description = "Mark as featured"
    
    def remove_featured(self, request, queryset):
        """Remove featured status from programs."""
        count = queryset.update(is_featured=False)
        self.message_user(request, f"{count} programs removed from featured.")
    remove_featured.short_description = "Remove featured status"
    
    def export_to_csv(self, request, queryset):
        """Export selected programs to CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="ministry_programs.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Code', 'Title', 'Ministry', 'Type', 'Status', 'Start Date', 'End Date',
            'Budget', 'Beneficiaries', 'Created By', 'Created At'
        ])
        
        for program in queryset:
            writer.writerow([
                program.code,
                program.title,
                program.get_ministry_display(),
                program.get_ppa_type_display(),
                program.get_status_display(),
                program.start_date,
                program.end_date,
                program.total_budget,
                program.estimated_beneficiaries,
                program.created_by.get_full_name() if program.created_by else '',
                program.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    export_to_csv.short_description = "Export to CSV"


@admin.register(MinistryProgramHistory)
class MinistryProgramHistoryAdmin(admin.ModelAdmin):
    """Admin for viewing program change history."""
    
    list_display = [
        'program', 'action_type', 'changed_by', 'changed_at', 'has_changes'
    ]
    
    list_filter = [
        'action_type', 'changed_at', 'program__ministry'
    ]
    
    search_fields = [
        'program__title', 'program__code', 'changed_by__first_name', 
        'changed_by__last_name', 'reason'
    ]
    
    readonly_fields = [
        'program', 'action_type', 'changed_fields', 'old_values', 'new_values',
        'reason', 'comments', 'changed_by', 'changed_at', 'ip_address', 'user_agent'
    ]
    
    date_hierarchy = 'changed_at'
    
    ordering = ['-changed_at']
    
    def has_add_permission(self, request):
        """History records should not be manually created."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """History records should be read-only."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """History records should not be deleted."""
        return False
    
    def has_changes(self, obj):
        """Display if there were field changes."""
        return len(obj.changed_fields) > 0
    has_changes.boolean = True
    has_changes.short_description = 'Has Changes'