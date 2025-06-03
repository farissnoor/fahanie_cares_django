from django.contrib import admin
from django.utils.html import format_html
from .models import Staff, StaffSupervisor, StaffTeam, StaffAttendance, StaffPerformance


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'position', 'division', 'employment_status', 
        'office', 'is_active', 'has_user_account_display', 'date_hired'
    ]
    list_filter = [
        'division', 'employment_status', 'office', 'is_active', 'date_hired'
    ]
    search_fields = ['full_name', 'position', 'email', 'phone_number']
    readonly_fields = ['notion_id', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'full_name', 'position', 'profile_image', 'bio')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone_number', 'address')
        }),
        ('Organizational Information', {
            'fields': ('division', 'office', 'employment_status', 'date_hired')
        }),
        ('Role and Responsibilities', {
            'fields': ('duties_responsibilities', 'staff_workflow')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('System Information', {
            'fields': ('notion_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_user_account_display(self, obj):
        if obj.has_user_account:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    has_user_account_display.short_description = 'Has User Account'
    has_user_account_display.allow_tags = True


@admin.register(StaffSupervisor)
class StaffSupervisorAdmin(admin.ModelAdmin):
    list_display = ['staff', 'supervisor', 'created_at']
    list_filter = ['supervisor__division', 'created_at']
    search_fields = ['staff__full_name', 'supervisor__full_name']
    autocomplete_fields = ['staff', 'supervisor']


@admin.register(StaffTeam)
class StaffTeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'team_lead', 'division', 'member_count', 'is_active']
    list_filter = ['division', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['members']
    fieldsets = (
        ('Team Information', {
            'fields': ('name', 'description', 'team_lead', 'division')
        }),
        ('Members', {
            'fields': ('members',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['created_at', 'updated_at']
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'staff', 'date', 'status', 'time_in', 'time_out', 
        'hours_worked_display', 'is_approved'
    ]
    list_filter = [
        'status', 'is_approved', 'date', 'staff__division'
    ]
    search_fields = ['staff__full_name', 'notes']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at', 'hours_worked_display']
    fieldsets = (
        ('Attendance Information', {
            'fields': ('staff', 'date', 'status')
        }),
        ('Time Tracking', {
            'fields': ('time_in', 'time_out', 'hours_worked_display')
        }),
        ('Notes and Approval', {
            'fields': ('notes', 'approved_by', 'is_approved')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def hours_worked_display(self, obj):
        hours = obj.hours_worked
        if hours > 0:
            return f"{hours:.2f} hours"
        return "Not calculated"
    hours_worked_display.short_description = 'Hours Worked'


@admin.register(StaffPerformance)
class StaffPerformanceAdmin(admin.ModelAdmin):
    list_display = [
        'staff', 'evaluation_period', 'period_start', 'period_end',
        'overall_rating_display', 'evaluated_by', 'evaluation_date'
    ]
    list_filter = [
        'evaluation_period', 'overall_rating', 'evaluation_date',
        'staff__division'
    ]
    search_fields = ['staff__full_name', 'evaluator_comments', 'strengths']
    date_hierarchy = 'evaluation_date'
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Evaluation Information', {
            'fields': ('staff', 'evaluation_period', 'period_start', 'period_end', 'evaluation_date', 'evaluated_by')
        }),
        ('Performance Ratings', {
            'fields': ('overall_rating', 'quality_of_work', 'punctuality', 'teamwork', 'communication', 'initiative')
        }),
        ('Comments and Goals', {
            'fields': ('strengths', 'areas_for_improvement', 'goals_next_period', 'evaluator_comments')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def overall_rating_display(self, obj):
        rating_colors = {
            5: 'green',
            4: 'lightgreen', 
            3: 'orange',
            2: 'red',
            1: 'darkred'
        }
        color = rating_colors.get(obj.overall_rating, 'black')
        rating_text = dict(obj.PERFORMANCE_RATING_CHOICES).get(obj.overall_rating, 'Unknown')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ({})</span>',
            color, rating_text, obj.overall_rating
        )
    overall_rating_display.short_description = 'Overall Rating'
    overall_rating_display.allow_tags = True