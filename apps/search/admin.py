from django.contrib import admin
from .models import SavedSearch, SearchHistory, SearchSuggestion


@admin.register(SavedSearch)
class SavedSearchAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'module', 'is_public', 'use_count', 'created_at', 'last_used']
    list_filter = ['module', 'is_public', 'created_at']
    search_fields = ['name', 'query', 'user__email']
    readonly_fields = ['id', 'created_at', 'last_used', 'use_count']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'name', 'module', 'is_public')
        }),
        ('Search Details', {
            'fields': ('query', 'filters'),
        }),
        ('Statistics', {
            'fields': ('use_count', 'created_at', 'last_used'),
        }),
    )


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'query', 'module', 'result_count', 'search_duration', 'created_at']
    list_filter = ['module', 'created_at']
    search_fields = ['query', 'user__email']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'module')
        }),
        ('Search Details', {
            'fields': ('query', 'filters', 'result_count', 'search_duration'),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SearchSuggestion)
class SearchSuggestionAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'frequency', 'module', 'last_used']
    list_filter = ['module', 'last_used']
    search_fields = ['keyword']
    readonly_fields = ['last_used']
    
    fieldsets = (
        (None, {
            'fields': ('keyword', 'module')
        }),
        ('Statistics', {
            'fields': ('frequency', 'last_used'),
        }),
    )
    
    def has_add_permission(self, request):
        return False