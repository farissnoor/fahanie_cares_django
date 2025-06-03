from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class SavedSearch(models.Model):
    """Model for saving user search queries and filters."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=255)
    query = models.CharField(max_length=500, blank=True)
    filters = models.JSONField(default=dict)
    module = models.CharField(max_length=50, choices=[
        ('all', 'All'),
        ('constituents', 'Constituents'),
        ('referrals', 'Referrals'),
        ('chapters', 'Chapters'),
        ('services', 'Services'),
        ('documents', 'Documents'),
        ('parliamentary', 'Parliamentary'),
    ])
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    use_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-last_used']
    
    def __str__(self):
        return f"{self.name} ({self.user.email})"
    
    def increment_use_count(self):
        """Increment the use count and update last used timestamp."""
        self.use_count += 1
        self.save()


class SearchHistory(models.Model):
    """Model for tracking user search history."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    query = models.CharField(max_length=500)
    module = models.CharField(max_length=50, choices=[
        ('all', 'All'),
        ('constituents', 'Constituents'),
        ('referrals', 'Referrals'),
        ('chapters', 'Chapters'),
        ('services', 'Services'),
        ('documents', 'Documents'),
        ('parliamentary', 'Parliamentary'),
    ])
    filters = models.JSONField(default=dict)
    result_count = models.IntegerField(default=0)
    search_duration = models.FloatField(null=True, blank=True)  # in seconds
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.query} by {self.user.email} at {self.created_at}"


class SearchSuggestion(models.Model):
    """Model for storing popular search suggestions."""
    keyword = models.CharField(max_length=255, unique=True)
    frequency = models.IntegerField(default=1)
    module = models.CharField(max_length=50, blank=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-frequency', '-last_used']
    
    def __str__(self):
        return f"{self.keyword} ({self.frequency})"
    
    @classmethod
    def update_suggestion(cls, keyword, module=''):
        """Update or create a search suggestion."""
        suggestion, created = cls.objects.get_or_create(
            keyword=keyword.lower(),
            defaults={'module': module}
        )
        if not created:
            suggestion.frequency += 1
            suggestion.save()
        return suggestion