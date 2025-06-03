import uuid
from django.db import models
from django.conf import settings
from apps.constituents.models import Constituent
from apps.referrals.models import Referral
from django.utils import timezone


class DocumentCategory(models.Model):
    """Categories for document organization."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subcategories')
    
    class Meta:
        verbose_name = 'Document Category'
        verbose_name_plural = 'Document Categories'
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Document(models.Model):
    """Document model for file uploads with version control."""
    DOCUMENT_STATUS = (
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    )
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='documents/%Y/%m/')
    file_size = models.BigIntegerField(default=0)
    file_type = models.CharField(max_length=50, blank=True)
    
    # Categorization
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    # Relationships
    constituent = models.ForeignKey(Constituent, on_delete=models.CASCADE, null=True, blank=True)
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, null=True, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=DOCUMENT_STATUS, default='draft')
    is_public = models.BooleanField(default=False)
    
    # Version control
    version = models.IntegerField(default=1)
    parent_document = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='versions')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notion integration
    notion_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['constituent', 'created_at']),
            models.Index(fields=['referral', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} (v{self.version})"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            # Extract file type from filename
            self.file_type = self.file.name.split('.')[-1].lower()
        super().save(*args, **kwargs)
    
    def create_new_version(self, file):
        """Create a new version of this document."""
        new_version = Document()
        # Copy all fields except id, file, and version
        for field in self._meta.fields:
            if field.name not in ['id', 'file', 'version', 'created_at', 'updated_at']:
                setattr(new_version, field.name, getattr(self, field.name))
        
        new_version.file = file
        new_version.version = self.version + 1
        new_version.parent_document = self.parent_document or self
        new_version.save()
        return new_version


class DocumentAccess(models.Model):
    """Track document access permissions and history."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=[
        ('view', 'View'),
        ('download', 'Download'),
        ('edit', 'Edit'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ])
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} {self.action} {self.document} at {self.timestamp}"


class DocumentTemplate(models.Model):
    """Reusable document templates."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True)
    file = models.FileField(upload_to='templates/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return self.name