from django.contrib import admin
from .models import (
    LegislativeSession, LegislativeMeasure, LegislativeAction,
    Committee, CommitteeMembership, CommitteeHearing,
    PlenarySession, SpeechPrivilege, OversightActivity, VotingRecord
)


@admin.register(LegislativeSession)
class LegislativeSessionAdmin(admin.ModelAdmin):
    list_display = ['congress_number', 'session_number', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current', 'congress_number']
    search_fields = ['congress_number', 'session_number', 'description']
    date_hierarchy = 'start_date'


class LegislativeActionInline(admin.TabularInline):
    model = LegislativeAction
    extra = 0
    fields = ['action_type', 'action_date', 'description', 'vote_yes', 'vote_no', 'vote_abstain']
    readonly_fields = ['action_date']


class VotingRecordInline(admin.TabularInline):
    model = VotingRecord
    extra = 0
    fields = ['member', 'vote', 'voting_session', 'reasoning']
    raw_id_fields = ['member', 'voting_session']


@admin.register(LegislativeMeasure)
class LegislativeMeasureAdmin(admin.ModelAdmin):
    list_display = ['number', 'measure_type', 'title', 'status', 'priority', 'filed_date', 'principal_author']
    list_filter = ['status', 'priority', 'measure_type', 'session']
    search_fields = ['number', 'title', 'short_title', 'abstract']
    date_hierarchy = 'filed_date'
    filter_horizontal = ['co_authors', 'related_measures']
    raw_id_fields = ['principal_author', 'created_by']
    inlines = [LegislativeActionInline, VotingRecordInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('session', 'measure_type', 'number', 'title', 'short_title', 'abstract', 'full_text_url')
        }),
        ('Authorship', {
            'fields': ('principal_author', 'co_authors')
        }),
        ('Status', {
            'fields': ('status', 'priority', 'filed_date', 'last_action_date')
        }),
        ('Committee', {
            'fields': ('primary_committee', 'secondary_committees')
        }),
        ('Relationships', {
            'fields': ('related_measures', 'supersedes')
        }),
        ('Impact', {
            'fields': ('beneficiaries', 'estimated_budget', 'implementation_timeline')
        }),
        ('Metadata', {
            'fields': ('is_public', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Committee)
class CommitteeAdmin(admin.ModelAdmin):
    list_display = ['name', 'acronym', 'committee_type', 'chairperson', 'is_active']
    list_filter = ['committee_type', 'is_active']
    search_fields = ['name', 'acronym', 'jurisdiction']
    raw_id_fields = ['chairperson', 'vice_chairperson', 'parent_committee']


class CommitteeMembershipInline(admin.TabularInline):
    model = CommitteeMembership
    extra = 0
    fields = ['member', 'role', 'start_date', 'end_date', 'is_active']
    raw_id_fields = ['member']


@admin.register(CommitteeMembership)
class CommitteeMembershipAdmin(admin.ModelAdmin):
    list_display = ['member', 'committee', 'role', 'start_date', 'end_date', 'is_active']
    list_filter = ['role', 'is_active', 'committee']
    search_fields = ['member__first_name', 'member__last_name', 'committee__name']
    date_hierarchy = 'start_date'
    raw_id_fields = ['member', 'committee']


@admin.register(CommitteeHearing)
class CommitteeHearingAdmin(admin.ModelAdmin):
    list_display = ['title', 'committee', 'hearing_type', 'scheduled_date', 'is_public']
    list_filter = ['hearing_type', 'is_public', 'committee']
    search_fields = ['title', 'description']
    date_hierarchy = 'scheduled_date'
    filter_horizontal = ['measures']
    raw_id_fields = ['committee', 'created_by']


@admin.register(PlenarySession)
class PlenarySessionAdmin(admin.ModelAdmin):
    list_display = ['session_date', 'session_type', 'session', 'start_time', 'end_time']
    list_filter = ['session_type', 'session']
    date_hierarchy = 'session_date'
    raw_id_fields = ['session']


@admin.register(SpeechPrivilege)
class SpeechPrivilegeAdmin(admin.ModelAdmin):
    list_display = ['title', 'speaker', 'speech_type', 'plenary_session', 'start_time']
    list_filter = ['speech_type', 'plenary_session__session_date']
    search_fields = ['title', 'summary']
    raw_id_fields = ['speaker', 'plenary_session', 'related_measure']


@admin.register(OversightActivity)
class OversightActivityAdmin(admin.ModelAdmin):
    list_display = ['title', 'activity_type', 'status', 'target_agency', 'start_date', 'lead_member']
    list_filter = ['activity_type', 'status', 'requires_followup']
    search_fields = ['title', 'description', 'target_agency', 'target_program']
    date_hierarchy = 'start_date'
    raw_id_fields = ['committee', 'lead_member', 'created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'activity_type', 'description', 'committee', 'lead_member')
        }),
        ('Target', {
            'fields': ('target_agency', 'target_program')
        }),
        ('Timeline', {
            'fields': ('status', 'start_date', 'end_date')
        }),
        ('Findings', {
            'fields': ('key_findings', 'recommendations')
        }),
        ('Documentation', {
            'fields': ('report_url', 'presentation_url')
        }),
        ('Follow-up', {
            'fields': ('requires_followup', 'followup_deadline')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']