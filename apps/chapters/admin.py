from django.contrib import admin
from .models import Chapter, ChapterMembership, ChapterActivity, ActivityAttendance

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'municipality', 'status', 'member_count', 'created_at']
    list_filter = ['tier', 'status', 'province', 'municipality']
    search_fields = ['name', 'municipality', 'description']
    ordering = ['tier', 'name']
    
    def get_queryset(self, request):
        # Only show provincial and municipal chapters in admin
        return super().get_queryset(request).filter(tier__in=['provincial', 'municipal'])

@admin.register(ChapterMembership)
class ChapterMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'chapter', 'role', 'status', 'joined_date']
    list_filter = ['status', 'role', 'chapter__tier', 'is_volunteer']
    search_fields = ['user__first_name', 'user__last_name', 'chapter__name']
    
    def get_queryset(self, request):
        # Only show memberships for provincial and municipal chapters
        return super().get_queryset(request).filter(chapter__tier__in=['provincial', 'municipal'])

@admin.register(ChapterActivity)
class ChapterActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'chapter', 'activity_type', 'date', 'status']
    list_filter = ['activity_type', 'status', 'chapter__tier']
    search_fields = ['title', 'chapter__name', 'description']
    ordering = ['-date']
    
    def get_queryset(self, request):
        # Only show activities for provincial and municipal chapters
        return super().get_queryset(request).filter(chapter__tier__in=['provincial', 'municipal'])

@admin.register(ActivityAttendance)
class ActivityAttendanceAdmin(admin.ModelAdmin):
    list_display = ['attendee', 'activity', 'status', 'check_in_time']
    list_filter = ['status', 'activity__activity_type']
    search_fields = ['attendee__first_name', 'attendee__last_name', 'activity__title']
    
    def get_queryset(self, request):
        # Only show attendance for provincial and municipal chapter activities
        return super().get_queryset(request).filter(activity__chapter__tier__in=['provincial', 'municipal'])
