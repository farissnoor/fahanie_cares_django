from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from apps.constituents.models import Constituent

class ServiceProgram(models.Model):
    """
    Direct service programs offered by #FahanieCares.
    """
    PROGRAM_STATUS = (
        ('active', 'Active'),
        ('planning', 'Planning'),
        ('completed', 'Completed'),
        ('suspended', 'Suspended'),
    )
    
    PROGRAM_TYPES = (
        ('educational', 'Educational Support'),
        ('health', 'Healthcare Services'),
        ('livelihood', 'Livelihood Assistance'),
        ('emergency', 'Emergency Relief'),
        ('infrastructure', 'Community Infrastructure'),
        ('social', 'Social Services'),
        ('youth', 'Youth Development'),
        ('elderly', 'Senior Citizen Support'),
        ('pwd', 'PWD Assistance'),
        ('other', 'Other Services'),
    )
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    program_type = models.CharField(max_length=20, choices=PROGRAM_TYPES)
    description = models.TextField()
    objectives = models.TextField()
    
    # Eligibility
    eligibility_criteria = models.TextField()
    required_documents = models.TextField()
    target_beneficiaries = models.CharField(max_length=200)
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    application_start = models.DateField(null=True, blank=True)
    application_end = models.DateField(null=True, blank=True)
    
    # Resources
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    funding_source = models.CharField(max_length=200, blank=True)
    max_beneficiaries = models.PositiveIntegerField(default=0)
    
    # Implementation
    status = models.CharField(max_length=20, choices=PROGRAM_STATUS, default='planning')
    implementing_chapters = models.ManyToManyField(
        'chapters.Chapter',
        related_name='programs',
        blank=True
    )
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='coordinated_programs'
    )
    
    # Partnerships
    partner_agencies = models.TextField(blank=True)
    partner_organizations = models.TextField(blank=True)
    
    # Documentation
    program_guidelines = models.FileField(upload_to='program_guidelines/', blank=True, null=True)
    application_form = models.FileField(upload_to='program_forms/', blank=True, null=True)
    
    # Tracking
    beneficiary_count = models.PositiveIntegerField(default=0)
    budget_utilized = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notion_id = models.CharField(max_length=36, blank=True, help_text="Notion database ID")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_programs'
    )
    
    class Meta:
        ordering = ['-start_date', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('service_program_detail', args=[self.slug])
    
    def is_accepting_applications(self):
        """Check if program is currently accepting applications."""
        if not self.application_start or not self.application_end:
            return self.status == 'active'
        
        today = timezone.now().date()
        return (self.application_start <= today <= self.application_end and 
                self.status == 'active')
    
    def update_beneficiary_count(self):
        """Update the beneficiary count based on approved applications."""
        self.beneficiary_count = self.applications.filter(
            status='approved'
        ).count()
        self.save(update_fields=['beneficiary_count'])


class ServiceApplication(models.Model):
    """
    Applications for direct service programs.
    """
    APPLICATION_STATUS = (
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('waitlisted', 'Waitlisted'),
        ('withdrawn', 'Withdrawn'),
    )
    
    PRIORITY_LEVELS = (
        ('urgent', 'Urgent'),
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low'),
    )
    
    # Application details
    application_number = models.CharField(max_length=20, unique=True)
    program = models.ForeignKey(
        ServiceProgram,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_applications'
    )
    
    # Beneficiary information (if different from applicant)
    beneficiary_is_self = models.BooleanField(default=True)
    beneficiary_name = models.CharField(max_length=200, blank=True)
    beneficiary_relationship = models.CharField(max_length=100, blank=True)
    beneficiary_contact = models.CharField(max_length=100, blank=True)
    
    # Application content
    household_size = models.PositiveSmallIntegerField(default=1)
    household_income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reason_for_application = models.TextField()
    supporting_details = models.TextField(blank=True)
    
    # Assessment
    priority_level = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    assessment_notes = models.TextField(blank=True)
    home_visit_required = models.BooleanField(default=False)
    home_visit_completed = models.BooleanField(default=False)
    home_visit_report = models.TextField(blank=True)
    
    # Documents
    supporting_documents = models.FileField(upload_to='application_documents/', blank=True, null=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_applications'
    )
    
    # Assistance details (if approved)
    assistance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    assistance_description = models.TextField(blank=True)
    disbursement_date = models.DateField(null=True, blank=True)
    disbursement_method = models.CharField(max_length=100, blank=True)
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True)
    
    # Tracking
    notion_id = models.CharField(max_length=36, blank=True, help_text="Notion database ID")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('program', 'applicant')
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            # Generate unique application number
            prefix = f"APP-{self.program.slug[:3].upper()}"
            timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
            self.application_number = f"{prefix}-{timestamp}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.application_number} - {self.applicant.get_full_name()}"
    
    def submit(self):
        """Submit the application for review."""
        self.status = 'submitted'
        self.submitted_at = timezone.now()
        self.save()
    
    def approve(self, user, amount=None, description=None):
        """Approve the application."""
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.approved_by = user
        
        if amount:
            self.assistance_amount = amount
        if description:
            self.assistance_description = description
        
        self.save()
        
        # Update program beneficiary count
        self.program.update_beneficiary_count()
    
    def reject(self, user, reason=None):
        """Reject the application."""
        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        self.reviewed_by = user
        
        if reason:
            self.assessment_notes += f"\n\nRejection reason: {reason}"
        
        self.save()


class ServiceDisbursement(models.Model):
    """
    Tracking disbursements for approved applications.
    """
    DISBURSEMENT_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )
    
    DISBURSEMENT_METHODS = (
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('gcash', 'GCash'),
        ('in_kind', 'In-Kind'),
        ('voucher', 'Voucher'),
    )
    
    application = models.ForeignKey(
        ServiceApplication,
        on_delete=models.CASCADE,
        related_name='disbursements'
    )
    
    # Disbursement details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=DISBURSEMENT_METHODS)
    reference_number = models.CharField(max_length=100, blank=True)
    
    # Recipient details
    recipient_name = models.CharField(max_length=200)
    recipient_id_type = models.CharField(max_length=50, blank=True)
    recipient_id_number = models.CharField(max_length=50, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=DISBURSEMENT_STATUS, default='pending')
    scheduled_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    
    # Processing details
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_disbursements'
    )
    notes = models.TextField(blank=True)
    
    # Documentation
    receipt = models.FileField(upload_to='disbursement_receipts/', blank=True, null=True)
    supporting_docs = models.FileField(upload_to='disbursement_docs/', blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.application.application_number} - {self.amount}"
    
    def complete(self, user):
        """Mark disbursement as completed."""
        self.status = 'completed'
        self.actual_date = timezone.now().date()
        self.processed_by = user
        self.save()


class ServiceImpact(models.Model):
    """
    Impact tracking for service programs.
    """
    program = models.ForeignKey(
        ServiceProgram,
        on_delete=models.CASCADE,
        related_name='impact_reports'
    )
    
    # Reporting period
    report_date = models.DateField()
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Beneficiary impact
    total_beneficiaries = models.PositiveIntegerField(default=0)
    direct_beneficiaries = models.PositiveIntegerField(default=0)
    indirect_beneficiaries = models.PositiveIntegerField(default=0)
    
    # Geographic reach
    municipalities_served = models.TextField()
    barangays_served = models.TextField()
    
    # Financial impact
    total_disbursed = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_assistance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Outcomes
    success_stories = models.TextField(blank=True)
    challenges_faced = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    # Documentation
    impact_photos = models.FileField(upload_to='impact_photos/', blank=True, null=True)
    detailed_report = models.FileField(upload_to='impact_reports/', blank=True, null=True)
    
    # Metadata
    prepared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='impact_reports_prepared'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='impact_reports_reviewed'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-report_date']
        unique_together = ('program', 'period_start', 'period_end')
    
    def __str__(self):
        return f"{self.program.name} Impact Report - {self.report_date}"


class MinistryProgram(models.Model):
    """
    Ministry Programs, Projects & Activities (PPAs) with full administrative control.
    Supports CRUD operations, audit trails, and role-based management.
    """
    
    MINISTRIES = (
        ('mssd', 'Ministry of Social Services and Development'),
        ('mafar', 'Ministry of Agriculture, Fisheries and Agrarian Reform'),
        ('mtit', 'Ministry of Trade, Industry and Tourism'),
        ('mhe', 'Ministry of Higher Education'),
        ('mbasiced', 'Ministry of Basic, Higher and Technical Education'),
        ('moh', 'Ministry of Health'),
        ('mpwh', 'Ministry of Public Works and Highways'),
        ('motc', 'Ministry of Transportation and Communications'),
        ('mei', 'Ministry of Environment and Interior'),
        ('mle', 'Ministry of Labor and Employment'),
        ('other', 'Other Ministry/Office'),
    )
    
    PPA_TYPES = (
        ('program', 'Program'),
        ('project', 'Project'),
        ('activity', 'Activity'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('archived', 'Archived'),
    )
    
    FUNDING_SOURCES = (
        ('national', 'National Government'),
        ('regional', 'Regional Government (BARMM)'),
        ('local', 'Local Government Unit'),
        ('international', 'International Donor'),
        ('private', 'Private Sector'),
        ('mixed', 'Mixed Sources'),
    )
    
    # Basic Information
    code = models.CharField(max_length=50, unique=True, help_text="Unique ministry program code")
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    ministry = models.CharField(max_length=20, choices=MINISTRIES)
    ppa_type = models.CharField(max_length=20, choices=PPA_TYPES)
    
    # Detailed Description
    description = models.TextField(help_text="Comprehensive program description")
    objectives = models.TextField(help_text="Program objectives and goals")
    expected_outcomes = models.TextField(help_text="Expected outcomes and impacts")
    key_performance_indicators = models.TextField(help_text="KPIs for monitoring and evaluation")
    
    # Target Groups
    target_beneficiaries = models.TextField(help_text="Description of target beneficiaries")
    geographic_coverage = models.TextField(help_text="Geographic areas covered")
    estimated_beneficiaries = models.PositiveIntegerField(default=0)
    
    # Implementation Details
    implementation_strategy = models.TextField(help_text="How the program will be implemented")
    implementing_units = models.TextField(help_text="Responsible implementing units/offices")
    partner_agencies = models.TextField(blank=True, help_text="Partner agencies and organizations")
    
    # Financial Information
    total_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    allocated_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    utilized_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    funding_source = models.CharField(max_length=20, choices=FUNDING_SOURCES)
    funding_details = models.TextField(blank=True, help_text="Detailed funding information")
    
    # Timeline
    start_date = models.DateField()
    end_date = models.DateField()
    duration_months = models.PositiveIntegerField(help_text="Program duration in months")
    
    # Status and Management
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    PRIORITY_LEVELS = (
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    )
    priority_level = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    
    # Administrative Control
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_ministry_programs'
    )
    ministry_liaison = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='liaised_programs',
        help_text="Ministry liaison officer responsible for this program"
    )
    program_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_programs'
    )
    
    # Access Control
    is_public = models.BooleanField(default=True, help_text="Whether program is visible to public")
    is_featured = models.BooleanField(default=False, help_text="Featured program on homepage")
    requires_approval = models.BooleanField(default=True, help_text="Changes require approval")
    
    # Documentation
    program_document = models.FileField(upload_to='ministry_programs/documents/', blank=True, null=True)
    implementation_guidelines = models.FileField(upload_to='ministry_programs/guidelines/', blank=True, null=True)
    monitoring_framework = models.FileField(upload_to='ministry_programs/monitoring/', blank=True, null=True)
    
    # Integration
    notion_database_id = models.CharField(max_length=36, blank=True, help_text="Notion database ID")
    external_system_id = models.CharField(max_length=100, blank=True, help_text="External system reference")
    
    # Audit Trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='last_modified_programs'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_programs'
    )
    
    # Soft Delete
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_programs'
    )
    deletion_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at', 'ministry', 'title']
        indexes = [
            models.Index(fields=['ministry', 'status']),
            models.Index(fields=['status', 'is_deleted']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.ministry}-{self.title}")
        
        # Auto-generate code if not provided
        if not self.code:
            ministry_prefix = self.ministry.upper()
            year = self.start_date.year if self.start_date else timezone.now().year
            count = MinistryProgram.objects.filter(
                ministry=self.ministry,
                start_date__year=year
            ).count() + 1
            self.code = f"{ministry_prefix}-{year}-{count:03d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"[{self.get_ministry_display()}] {self.title}"
    
    def get_absolute_url(self):
        return reverse('ministry_program_detail', args=[self.slug])
    
    def soft_delete(self, user, reason=None):
        """Soft delete the program instead of hard delete."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        if reason:
            self.deletion_reason = reason
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by', 'deletion_reason'])
    
    def restore(self, user):
        """Restore a soft-deleted program."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = ''
        self.last_modified_by = user
        self.save()
    
    def approve(self, user):
        """Approve the program."""
        self.status = 'active'
        self.approved_at = timezone.now()
        self.approved_by = user
        self.last_modified_by = user
        self.save()
    
    def can_edit(self, user):
        """Check if user can edit this program."""
        if user.is_superuser:
            return True
        if user == self.created_by or user == self.ministry_liaison or user == self.program_manager:
            return True
        if user.user_type in ['staff', 'mp'] and not self.requires_approval:
            return True
        return False
    
    def can_delete(self, user):
        """Check if user can delete this program."""
        if user.is_superuser:
            return True
        if user == self.created_by and self.status == 'draft':
            return True
        if user.user_type in ['staff', 'mp']:
            return True
        return False
    
    def get_budget_utilization_percentage(self):
        """Calculate budget utilization percentage."""
        if self.allocated_budget > 0:
            return (self.utilized_budget / self.allocated_budget) * 100
        return 0
    
    def is_active(self):
        """Check if program is currently active."""
        return self.status == 'active' and not self.is_deleted
    
    @property
    def status_color(self):
        """Return CSS class for status badge color."""
        status_colors = {
            'draft': 'secondary',
            'pending_approval': 'warning',
            'active': 'success',
            'suspended': 'danger',
            'completed': 'info',
            'cancelled': 'dark',
            'archived': 'light',
        }
        return status_colors.get(self.status, 'secondary')


class MinistryProgramHistory(models.Model):
    """
    Track all changes made to ministry programs for audit purposes.
    """
    ACTION_TYPES = (
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('restore', 'Restored'),
        ('approve', 'Approved'),
        ('suspend', 'Suspended'),
        ('complete', 'Completed'),
    )
    
    program = models.ForeignKey(
        MinistryProgram,
        on_delete=models.CASCADE,
        related_name='history'
    )
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    changed_fields = models.JSONField(default=dict, help_text="Fields that were changed")
    old_values = models.JSONField(default=dict, help_text="Previous values")
    new_values = models.JSONField(default=dict, help_text="New values")
    
    # Change details
    reason = models.TextField(blank=True, help_text="Reason for the change")
    comments = models.TextField(blank=True)
    
    # User and timestamp
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='program_changes'
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    
    # System info
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['program', 'changed_at']),
            models.Index(fields=['action_type', 'changed_at']),
        ]
    
    def __str__(self):
        return f"{self.program.title} - {self.get_action_type_display()} by {self.changed_by.get_full_name()}"
