from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class Report(models.Model):
    """Model for saved reports."""
    REPORT_TYPES = [
        ('referrals', 'Referrals Report'),
        ('constituents', 'Constituents Report'),
        ('chapters', 'Chapters Report'),
        ('services', 'Services Report'),
        ('custom', 'Custom Report'),
    ]
    
    REPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    parameters = models.JSONField(default=dict)
    file_path = models.CharField(max_length=500, blank=True)
    format = models.CharField(max_length=10, choices=REPORT_FORMATS, default='pdf')
    is_scheduled = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"


class ScheduledReport(models.Model):
    """Model for scheduled reports."""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=Report.REPORT_TYPES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    parameters = models.JSONField(default=dict)
    recipients = models.ManyToManyField(User, related_name='scheduled_reports')
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_scheduled_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['next_run']
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"


class Dashboard(models.Model):
    """Model for custom dashboards."""
    DASHBOARD_TYPES = [
        ('executive', 'Executive Dashboard'),
        ('operational', 'Operational Dashboard'),
        ('chapter', 'Chapter Dashboard'),
        ('custom', 'Custom Dashboard'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    dashboard_type = models.CharField(max_length=20, choices=DASHBOARD_TYPES)
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_dashboards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    config = models.JSONField(default=dict)  # Widget configuration
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_dashboard_type_display()})"


class DashboardWidget(models.Model):
    """Model for dashboard widgets."""
    WIDGET_TYPES = [
        ('chart', 'Chart'),
        ('metric', 'Metric'),
        ('table', 'Table'),
        ('map', 'Map'),
        ('timeline', 'Timeline'),
    ]
    
    CHART_TYPES = [
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('pie', 'Pie Chart'),
        ('doughnut', 'Doughnut Chart'),
        ('area', 'Area Chart'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')
    title = models.CharField(max_length=255)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES, blank=True)
    data_source = models.CharField(max_length=100)  # e.g., 'referrals', 'constituents'
    filters = models.JSONField(default=dict)
    position = models.IntegerField(default=0)
    width = models.IntegerField(default=6)  # Grid system: 1-12
    height = models.IntegerField(default=300)  # Pixels
    config = models.JSONField(default=dict)  # Additional widget configuration
    
    class Meta:
        ordering = ['position']
    
    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"