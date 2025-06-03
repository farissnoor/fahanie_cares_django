from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Constituent, ConstituentInteraction, ConstituentGroup
from .member_models import FahanieCaresMember

class ConstituentInteractionInline(admin.TabularInline):
    model = ConstituentInteraction
    extra = 0
    fields = ('interaction_type', 'date', 'staff_member', 'description', 'outcome', 'is_completed')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        # Limit the displayed interactions to the most recent ones
        qs = super().get_queryset(request)
        return qs.order_by('-date')[:5]

@admin.register(Constituent)
class ConstituentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user_email', 'phone_number', 'membership_status', 'is_voter', 'engagement_level')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'user__phone_number')
    list_filter = ('is_voter', 'user__user_type', 'is_volunteer', 'gender', 'education_level')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'birth_date', 'gender', 'profile_image')
        }),
        ('Contact Information', {
            'fields': ('alternate_contact',)
        }),
        ('Demographics', {
            'fields': ('education_level', 'occupation', 'occupation_type', 'household_size')
        }),
        ('Voter Information', {
            'fields': ('is_voter', 'voter_id', 'voting_center')
        }),
        ('Membership Information', {
            'fields': ('membership_date', 'engagement_level', 'is_volunteer', 'volunteer_interests')
        }),
        ('Additional Information', {
            'fields': ('bio', 'interests', 'language_preference', 'notes')
        }),
        ('Metadata', {
            'fields': ('notion_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ConstituentInteractionInline]
    
    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    full_name.short_description = 'Name'
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def phone_number(self, obj):
        return obj.user.phone_number
    phone_number.short_description = 'Phone'
    
    def membership_status(self, obj):
        user_type = obj.user.user_type
        if user_type == 'constituent':
            return format_html('<span style="color: gray;">Basic</span>')
        elif user_type == 'member':
            return format_html('<span style="color: green;">Member</span>')
        elif user_type == 'chapter_member':
            return format_html('<span style="color: blue;">Chapter Member</span>')
        elif user_type == 'coordinator':
            return format_html('<span style="color: purple;">Coordinator</span>')
        return user_type
    membership_status.short_description = 'Membership'

@admin.register(ConstituentInteraction)
class ConstituentInteractionAdmin(admin.ModelAdmin):
    list_display = ('constituent_name', 'interaction_type', 'date', 'staff_member_name', 'outcome', 'is_completed')
    list_filter = ('interaction_type', 'outcome', 'is_completed', 'date')
    search_fields = ('constituent__user__first_name', 'constituent__user__last_name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Interaction Details', {
            'fields': ('constituent', 'interaction_type', 'date', 'staff_member', 'description')
        }),
        ('Outcome and Follow-up', {
            'fields': ('outcome', 'follow_up_date', 'follow_up_notes', 'is_completed')
        }),
        ('Location', {
            'fields': ('location',)
        }),
        ('Metadata', {
            'fields': ('notion_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def constituent_name(self, obj):
        return obj.constituent.user.get_full_name() or obj.constituent.user.username
    constituent_name.short_description = 'Constituent'
    
    def staff_member_name(self, obj):
        if obj.staff_member:
            return obj.staff_member.get_full_name() or obj.staff_member.username
        return '—'
    staff_member_name.short_description = 'Staff Member'

@admin.register(ConstituentGroup)
class ConstituentGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'member_count', 'created_by_name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('members',)
    
    fieldsets = (
        ('Group Information', {
            'fields': ('name', 'slug', 'description', 'is_active')
        }),
        ('Members', {
            'fields': ('members',)
        }),
        ('Management', {
            'fields': ('created_by',)
        }),
        ('Metadata', {
            'fields': ('notion_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def member_count(self, obj):
        count = obj.members.count()
        url = reverse('admin:constituents_constituent_changelist')
        return format_html('<a href="{}?groups__id__exact={}">{} members</a>', url, obj.id, count)
    member_count.short_description = 'Members'
    
    def created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return '—'
    created_by_name.short_description = 'Created By'


@admin.register(FahanieCaresMember)
class FahanieCaresMemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'contact_number', 'age', 'sector_display', 
                    'address_municipality', 'is_approved', 'date_of_application')
    list_filter = ('is_approved', 'sector', 'sex', 'highest_education', 'eligibility',
                   'is_volunteer_teacher', 'address_municipality', 'date_of_application')
    search_fields = ('last_name', 'first_name', 'middle_name', 'email', 'contact_number',
                     'address_barangay', 'address_municipality')
    readonly_fields = ('date_of_application', 'created_at', 'updated_at', 'user')
    date_hierarchy = 'date_of_application'
    
    fieldsets = (
        ('Application Information', {
            'fields': ('user', 'date_of_application', 'is_approved', 'approved_date', 'approved_by')
        }),
        ('Personal Information', {
            'fields': ('last_name', 'first_name', 'middle_name', 'contact_number', 
                      'email', 'age', 'sex')
        }),
        ('Current Address', {
            'fields': ('address_barangay', 'address_municipality', 'address_province')
        }),
        ('Voter Registration Address', {
            'fields': ('voter_address_barangay', 'voter_address_municipality', 'voter_address_province')
        }),
        ('Sector Information', {
            'fields': ('sector',)
        }),
        ('Education Information', {
            'fields': ('highest_education', 'school_graduated', 'eligibility')
        }),
        ('Volunteer Teacher Information', {
            'fields': ('is_volunteer_teacher', 'volunteer_school', 'volunteer_service_length'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('notion_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return f"{obj.last_name}, {obj.first_name} {obj.middle_name or ''}"
    full_name.short_description = 'Full Name'
    
    def sector_display(self, obj):
        return obj.get_sector_display()
    sector_display.short_description = 'Sector'
    
    def approve_members(self, request, queryset):
        """Admin action to approve selected members"""
        from django.utils import timezone
        count = queryset.update(
            is_approved=True, 
            approved_by=request.user,
            approved_date=timezone.now().date()
        )
        self.message_user(request, f"{count} members approved successfully.")
    approve_members.short_description = "Approve selected members"
    
    actions = [approve_members]
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'approved_by')
