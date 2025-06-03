from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q, Count
from datetime import date, timedelta


class LegislativeSession(models.Model):
    """Track legislative sessions and periods."""
    session_number = models.CharField(max_length=50)
    congress_number = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-start_date']
        unique_together = ['congress_number', 'session_number']
    
    def __str__(self):
        return f"{self.congress_number} Congress - {self.session_number} Session"
    
    def save(self, *args, **kwargs):
        if self.is_current:
            # Ensure only one current session
            LegislativeSession.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class LegislativeMeasure(models.Model):
    """Track bills, resolutions, and other legislative measures."""
    TYPE_CHOICES = (
        ('bill', 'House Bill'),
        ('resolution', 'House Resolution'),
        ('concurrent', 'Concurrent Resolution'),
        ('joint', 'Joint Resolution'),
        ('ordinance', 'Local Ordinance'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('filed', 'Filed'),
        ('committee', 'In Committee'),
        ('plenary', 'Plenary Deliberation'),
        ('approved_house', 'Approved on Third Reading'),
        ('transmitted', 'Transmitted to Senate'),
        ('bicameral', 'Bicameral Conference'),
        ('enrolled', 'Enrolled'),
        ('enacted', 'Enacted into Law'),
        ('vetoed', 'Vetoed'),
        ('archived', 'Archived'),
    )
    
    PRIORITY_CHOICES = (
        ('urgent', 'Urgent'),
        ('high', 'High Priority'),
        ('normal', 'Normal'),
        ('low', 'Low Priority'),
    )
    
    # Core fields
    session = models.ForeignKey(LegislativeSession, on_delete=models.PROTECT, related_name='measures')
    measure_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    number = models.CharField(max_length=50)
    title = models.CharField(max_length=500)
    short_title = models.CharField(max_length=200, blank=True)
    abstract = models.TextField()
    full_text_url = models.URLField(blank=True)
    
    # Authorship
    principal_author = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='principal_measures'
    )
    co_authors = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='co_authored_measures', 
        blank=True
    )
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    filed_date = models.DateField(null=True, blank=True)
    last_action_date = models.DateField(null=True, blank=True)
    
    # Committee assignment
    primary_committee = models.CharField(max_length=200, blank=True)
    secondary_committees = models.TextField(blank=True, help_text="Comma-separated list")
    
    # Related legislation
    related_measures = models.ManyToManyField('self', blank=True)
    supersedes = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='superseded_by')
    
    # Impact tracking
    beneficiaries = models.TextField(blank=True, help_text="Target beneficiaries")
    estimated_budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    implementation_timeline = models.CharField(max_length=200, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_measures'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-filed_date', '-created_at']
        unique_together = ['session', 'measure_type', 'number']
    
    def __str__(self):
        return f"{self.get_measure_type_display()} {self.number}: {self.short_title or self.title[:50]}"
    
    def get_absolute_url(self):
        return reverse('parliamentary:measure_detail', kwargs={'pk': self.pk})
    
    @property
    def is_urgent(self):
        return self.priority == 'urgent'
    
    @property
    def days_since_filing(self):
        if self.filed_date:
            return (date.today() - self.filed_date).days
        return None


class LegislativeAction(models.Model):
    """Track actions taken on legislative measures."""
    ACTION_TYPES = (
        ('filed', 'Filed'),
        ('referred', 'Referred to Committee'),
        ('hearing', 'Committee Hearing'),
        ('approved_committee', 'Approved in Committee'),
        ('reported_out', 'Reported Out'),
        ('calendared', 'Calendared for Plenary'),
        ('plenary_debate', 'Plenary Debate'),
        ('vote', 'Voted On'),
        ('approved', 'Approved'),
        ('transmitted', 'Transmitted'),
        ('conference', 'Bicameral Conference'),
        ('enrolled', 'Enrolled'),
        ('signed', 'Signed into Law'),
        ('vetoed', 'Vetoed'),
    )
    
    measure = models.ForeignKey(LegislativeMeasure, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    action_date = models.DateTimeField(default=timezone.now)
    description = models.TextField()
    vote_yes = models.IntegerField(null=True, blank=True)
    vote_no = models.IntegerField(null=True, blank=True)
    vote_abstain = models.IntegerField(null=True, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='recorded_actions'
    )
    
    class Meta:
        ordering = ['-action_date']
    
    def __str__(self):
        return f"{self.measure.number} - {self.get_action_type_display()} ({self.action_date.date()})"


class Committee(models.Model):
    """Track legislative committees and their work."""
    COMMITTEE_TYPES = (
        ('standing', 'Standing Committee'),
        ('special', 'Special Committee'),
        ('joint', 'Joint Committee'),
        ('subcommittee', 'Subcommittee'),
        ('adhoc', 'Ad Hoc Committee'),
    )
    
    name = models.CharField(max_length=200)
    acronym = models.CharField(max_length=20, blank=True)
    committee_type = models.CharField(max_length=20, choices=COMMITTEE_TYPES)
    jurisdiction = models.TextField()
    parent_committee = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcommittees')
    
    # Leadership
    chairperson = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='chaired_committees'
    )
    vice_chairperson = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='vice_chaired_committees'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    established_date = models.DateField()
    dissolved_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.acronym or self.name
    
    @property
    def member_count(self):
        return self.memberships.filter(is_active=True).count()


class CommitteeMembership(models.Model):
    """Track committee memberships."""
    ROLE_CHOICES = (
        ('chairperson', 'Chairperson'),
        ('vice_chair', 'Vice Chairperson'),
        ('secretary', 'Secretary'),
        ('member', 'Member'),
        ('ex_officio', 'Ex Officio'),
    )
    
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='memberships')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='committee_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['committee', 'role', 'member']
        unique_together = ['committee', 'member', 'start_date']
    
    def __str__(self):
        return f"{self.member} - {self.committee} ({self.role})"


class CommitteeHearing(models.Model):
    """Track committee hearings and meetings."""
    HEARING_TYPES = (
        ('regular', 'Regular Meeting'),
        ('special', 'Special Meeting'),
        ('public', 'Public Hearing'),
        ('executive', 'Executive Session'),
        ('markup', 'Markup Session'),
    )
    
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='hearings')
    hearing_type = models.CharField(max_length=20, choices=HEARING_TYPES)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    scheduled_date = models.DateTimeField()
    actual_date = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200)
    
    # Related measures
    measures = models.ManyToManyField(LegislativeMeasure, related_name='hearings', blank=True)
    
    # Documentation
    agenda_url = models.URLField(blank=True)
    minutes_url = models.URLField(blank=True)
    recording_url = models.URLField(blank=True)
    
    # Attendance
    is_public = models.BooleanField(default=False)
    attendance_count = models.IntegerField(null=True, blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_hearings'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.committee.acronym} - {self.title} ({self.scheduled_date.date()})"


class PlenarySession(models.Model):
    """Track plenary sessions."""
    SESSION_TYPES = (
        ('regular', 'Regular Session'),
        ('special', 'Special Session'),
        ('joint', 'Joint Session'),
    )
    
    session = models.ForeignKey(LegislativeSession, on_delete=models.CASCADE, related_name='plenary_sessions')
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    
    # Documentation
    order_of_business_url = models.URLField(blank=True)
    journal_url = models.URLField(blank=True)
    transcript_url = models.URLField(blank=True)
    
    # Attendance
    present_count = models.IntegerField(null=True, blank=True)
    absent_count = models.IntegerField(null=True, blank=True)
    
    # Key events
    key_events = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-session_date', '-start_time']
    
    def __str__(self):
        return f"{self.get_session_type_display()} - {self.session_date}"


class SpeechPrivilege(models.Model):
    """Track privilege speeches and manifestations."""
    SPEECH_TYPES = (
        ('privilege_personal', 'Privilege Speech - Personal'),
        ('privilege_collective', 'Privilege Speech - Collective'),
        ('manifestation', 'Manifestation'),
        ('sponsorship', 'Sponsorship Speech'),
        ('interpellation', 'Interpellation'),
        ('explanation', 'Explanation of Vote'),
    )
    
    plenary_session = models.ForeignKey(PlenarySession, on_delete=models.CASCADE, related_name='speeches')
    speaker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='speeches')
    speech_type = models.CharField(max_length=30, choices=SPEECH_TYPES)
    title = models.CharField(max_length=300)
    summary = models.TextField()
    
    # Related measure (if applicable)
    related_measure = models.ForeignKey(
        LegislativeMeasure, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='speeches'
    )
    
    # Documentation
    full_text_url = models.URLField(blank=True)
    video_url = models.URLField(blank=True)
    
    # Timing
    start_time = models.TimeField()
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['plenary_session', 'start_time']
    
    def __str__(self):
        return f"{self.speaker} - {self.title} ({self.plenary_session.session_date})"


class OversightActivity(models.Model):
    """Track oversight activities including investigations and monitoring."""
    ACTIVITY_TYPES = (
        ('investigation', 'Investigation'),
        ('monitoring', 'Monitoring'),
        ('audit', 'Audit Review'),
        ('inspection', 'Site Inspection'),
        ('inquiry', 'Inquiry'),
        ('hearing', 'Oversight Hearing'),
    )
    
    STATUS_CHOICES = (
        ('planned', 'Planned'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    )
    
    title = models.CharField(max_length=300)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    committee = models.ForeignKey(Committee, on_delete=models.SET_NULL, null=True, blank=True, related_name='oversight_activities')
    lead_member = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='led_oversight'
    )
    
    # Target
    target_agency = models.CharField(max_length=200)
    target_program = models.CharField(max_length=200, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Findings
    key_findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    # Documentation
    report_url = models.URLField(blank=True)
    presentation_url = models.URLField(blank=True)
    
    # Follow-up
    requires_followup = models.BooleanField(default=False)
    followup_deadline = models.DateField(null=True, blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_oversight'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = "Oversight activities"
    
    def __str__(self):
        return f"{self.get_activity_type_display()}: {self.title}"
    
    @property
    def is_overdue(self):
        return self.followup_deadline and date.today() > self.followup_deadline and self.status != 'completed'


class VotingRecord(models.Model):
    """Track voting records for measures."""
    VOTE_CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
        ('abstain', 'Abstain'),
        ('absent', 'Absent'),
    )
    
    measure = models.ForeignKey(LegislativeMeasure, on_delete=models.CASCADE, related_name='votes')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='voting_records')
    vote = models.CharField(max_length=10, choices=VOTE_CHOICES)
    voting_session = models.ForeignKey(PlenarySession, on_delete=models.CASCADE, related_name='votes')
    reasoning = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['measure', 'member', 'voting_session']
    
    def __str__(self):
        return f"{self.member} - {self.measure.number}: {self.vote}"