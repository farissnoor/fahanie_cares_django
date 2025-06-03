import time
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from typing import Dict, List, Optional, Any
from utils.notion.client import NotionService
from .models import SearchHistory, SearchSuggestion
import logging

logger = logging.getLogger(__name__)


class SearchService:
    """Service for handling global and module-specific searches."""
    
    def __init__(self, notion_service: NotionService = None):
        self.notion_service = notion_service or NotionService()
        self.databases = {
            'constituents': getattr(settings, 'NOTION_CONSTITUENTS_DATABASE', ''),
            'referrals': getattr(settings, 'NOTION_REFERRALS_DATABASE', ''),
            'chapters': getattr(settings, 'NOTION_CHAPTER_DATABASE', ''),
            'services': getattr(settings, 'NOTION_SERVICES_DATABASE', ''),
            'documents': getattr(settings, 'NOTION_DOCUMENTS_DATABASE', ''),
            'parliamentary': getattr(settings, 'NOTION_LEGISLATION_DATABASE', ''),
        }
    
    def global_search(self, query: str, user=None, limit: int = 10) -> Dict[str, List]:
        """Perform a global search across all modules."""
        start_time = time.time()
        results = {}
        total_results = 0
        
        # Check cache first
        cache_key = f"global_search:{query.lower()}:{limit}"
        cached_results = cache.get(cache_key)
        if cached_results:
            return cached_results
        
        # Search each database
        for module, database_id in self.databases.items():
            if database_id:
                try:
                    module_results = self._search_module(module, database_id, query, limit)
                    if module_results:
                        results[module] = module_results
                        total_results += len(module_results)
                except Exception as e:
                    logger.error(f"Error searching {module}: {str(e)}")
        
        # Store search history
        search_duration = time.time() - start_time
        if user and user.is_authenticated:
            SearchHistory.objects.create(
                user=user,
                query=query,
                module='all',
                result_count=total_results,
                search_duration=search_duration
            )
        
        # Update search suggestions
        SearchSuggestion.update_suggestion(query, 'all')
        
        # Cache results
        cache.set(cache_key, results, 300)  # Cache for 5 minutes
        
        return results
    
    def search_module(self, module: str, query: str = None, filters: Dict = None, 
                      sort: Dict = None, limit: int = None, user=None) -> List:
        """Search within a specific module."""
        database_id = self.databases.get(module)
        if not database_id:
            raise ValueError(f"Unknown module: {module}")
        
        start_time = time.time()
        
        try:
            results = self._search_module(module, database_id, query, limit, filters, sort)
            
            # Store search history
            search_duration = time.time() - start_time
            if user and user.is_authenticated:
                SearchHistory.objects.create(
                    user=user,
                    query=query or '',
                    module=module,
                    filters=filters or {},
                    result_count=len(results),
                    search_duration=search_duration
                )
            
            # Update search suggestions if query provided
            if query:
                SearchSuggestion.update_suggestion(query, module)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching {module}: {str(e)}")
            raise
    
    def _search_module(self, module: str, database_id: str, query: str = None, 
                       limit: int = None, filters: Dict = None, sort: Dict = None) -> List:
        """Internal method to search a specific module."""
        filter_params = self._build_search_filter(module, query, filters)
        
        try:
            results = self.notion_service.query_database(
                database_id,
                filter=filter_params if filter_params else None,
                sorts=sort
            )
            
            # Apply limit
            if limit:
                results = results[:limit]
            
            # Process results based on module type
            return self._process_results(module, results)
            
        except Exception as e:
            logger.error(f"Error querying {module} database: {str(e)}")
            return []
    
    def _build_search_filter(self, module: str, query: str = None, filters: Dict = None) -> Dict:
        """Build Notion API filter based on module type and search parameters."""
        filter_conditions = []
        
        # Add text search if query provided
        if query:
            if module == 'constituents':
                filter_conditions.append({
                    'or': [
                        {'property': 'Name', 'title': {'contains': query}},
                        {'property': 'Contact Number', 'phone_number': {'contains': query}},
                        {'property': 'Email', 'email': {'contains': query}},
                        {'property': 'Address', 'rich_text': {'contains': query}}
                    ]
                })
            elif module == 'referrals':
                filter_conditions.append({
                    'or': [
                        {'property': 'Title', 'title': {'contains': query}},
                        {'property': 'Description', 'rich_text': {'contains': query}},
                        {'property': 'Notes', 'rich_text': {'contains': query}},
                        {'property': 'Reference Number', 'rich_text': {'contains': query}}
                    ]
                })
            elif module == 'documents':
                filter_conditions.append({
                    'or': [
                        {'property': 'Title', 'title': {'contains': query}},
                        {'property': 'Description', 'rich_text': {'contains': query}},
                        {'property': 'Tags', 'multi_select': {'contains': query}}
                    ]
                })
            else:
                # Default search on title property
                filter_conditions.append({'property': 'Title', 'title': {'contains': query}})
        
        # Add additional filters if provided
        if filters:
            for field, value in filters.items():
                if module == 'constituents':
                    if field == 'municipality' and value:
                        filter_conditions.append({'property': 'Municipality', 'select': {'equals': value}})
                    elif field == 'barangay' and value:
                        filter_conditions.append({'property': 'Barangay', 'select': {'equals': value}})
                    elif field == 'chapter_member' and value:
                        filter_conditions.append({'property': 'Chapter Member', 'checkbox': {'equals': True}})
                elif module == 'referrals':
                    if field == 'status' and value:
                        filter_conditions.append({'property': 'Status', 'select': {'equals': value}})
                    elif field == 'category' and value:
                        filter_conditions.append({'property': 'Category', 'select': {'equals': value}})
                    elif field == 'priority' and value:
                        filter_conditions.append({'property': 'Priority', 'select': {'equals': value}})
                # Add more module-specific filters as needed
        
        # Combine filter conditions
        if len(filter_conditions) > 1:
            return {'and': filter_conditions}
        elif len(filter_conditions) == 1:
            return filter_conditions[0]
        else:
            return {}
    
    def _process_results(self, module: str, results: List) -> List:
        """Process raw Notion results into standardized format."""
        processed = []
        
        for result in results:
            processed_item = {
                'id': result.get('id'),
                'module': module,
                'created_time': result.get('created_time'),
                'last_edited_time': result.get('last_edited_time'),
                'properties': {}
            }
            
            # Extract relevant properties based on module
            properties = result.get('properties', {})
            
            if module == 'constituents':
                processed_item['properties'] = {
                    'name': self._extract_property(properties.get('Name')),
                    'contact_number': self._extract_property(properties.get('Contact Number')),
                    'email': self._extract_property(properties.get('Email')),
                    'municipality': self._extract_property(properties.get('Municipality')),
                    'barangay': self._extract_property(properties.get('Barangay')),
                }
                processed_item['display_title'] = processed_item['properties']['name']
                
            elif module == 'referrals':
                processed_item['properties'] = {
                    'title': self._extract_property(properties.get('Title')),
                    'reference_number': self._extract_property(properties.get('Reference Number')),
                    'status': self._extract_property(properties.get('Status')),
                    'category': self._extract_property(properties.get('Category')),
                    'priority': self._extract_property(properties.get('Priority')),
                }
                processed_item['display_title'] = processed_item['properties']['title']
                
            else:
                # Default properties
                processed_item['properties'] = {
                    'title': self._extract_property(properties.get('Title', properties.get('Name'))),
                }
                processed_item['display_title'] = processed_item['properties']['title']
            
            processed.append(processed_item)
        
        return processed
    
    def _extract_property(self, property_value: Dict) -> Any:
        """Extract value from Notion property format."""
        if not property_value:
            return None
        
        prop_type = property_value.get('type')
        
        if prop_type == 'title':
            title_array = property_value.get('title', [])
            return title_array[0].get('text', {}).get('content', '') if title_array else ''
        elif prop_type == 'rich_text':
            text_array = property_value.get('rich_text', [])
            return text_array[0].get('text', {}).get('content', '') if text_array else ''
        elif prop_type == 'number':
            return property_value.get('number')
        elif prop_type == 'select':
            return property_value.get('select', {}).get('name', '')
        elif prop_type == 'multi_select':
            return [item.get('name', '') for item in property_value.get('multi_select', [])]
        elif prop_type == 'date':
            date_value = property_value.get('date', {})
            return date_value.get('start') if date_value else None
        elif prop_type == 'checkbox':
            return property_value.get('checkbox', False)
        elif prop_type == 'url':
            return property_value.get('url', '')
        elif prop_type == 'email':
            return property_value.get('email', '')
        elif prop_type == 'phone_number':
            return property_value.get('phone_number', '')
        
        return None
    
    def get_search_suggestions(self, query: str, module: str = None, limit: int = 10) -> List[str]:
        """Get search suggestions based on partial query."""
        suggestions = SearchSuggestion.objects.filter(
            keyword__istartswith=query.lower()
        )
        
        if module:
            suggestions = suggestions.filter(
                Q(module=module) | Q(module='')
            )
        
        suggestions = suggestions[:limit]
        
        return [s.keyword for s in suggestions]
    
    def get_popular_searches(self, module: str = None, limit: int = 5) -> List[str]:
        """Get popular searches for a module."""
        suggestions = SearchSuggestion.objects.all()
        
        if module:
            suggestions = suggestions.filter(
                Q(module=module) | Q(module='')
            )
        
        suggestions = suggestions[:limit]
        
        return [s.keyword for s in suggestions]