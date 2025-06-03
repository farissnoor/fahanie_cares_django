"""
Notion API client service for #FahanieCares.
Handles all interactions with the Notion API, including rate limiting, caching, and error handling.
"""

import time
import logging
from typing import Dict, List, Optional, Any, Union
from notion_client import Client
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class NotionService:
    """
    Service class for interacting with the Notion API.
    Implements rate limiting, caching, and pagination for handling large datasets.
    """
    def __init__(self, token=None):
        """
        Initialize the Notion client with the provided token or from settings.
        """
        self.token = token or getattr(settings, 'NOTION_API_KEY', '')
        if self.token:
            self.client = Client(auth=self.token)
            self.rate_limit = 3  # requests per second (Notion's limit)
            self.last_request_time = 0
            self._init_specialized_services()
        else:
            logger.warning("No Notion API key provided - Notion integration is disabled")
            self.client = None
            
    def _init_specialized_services(self):
        """
        Initialize specialized services for different data types.
        These are loaded lazily to avoid circular imports.
        """
        try:
            from .referrals import ReferralNotionService
            self._referral_service = ReferralNotionService(self.token)
        except ImportError:
            logger.warning("ReferralNotionService could not be imported")
            self._referral_service = None
            
    def _respect_rate_limit(self):
        """
        Ensure requests don't exceed Notion's rate limit.
        Sleeps if necessary to stay within the limit.
        """
        if not self.client:
            return
            
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < (1 / self.rate_limit):
            sleep_time = (1 / self.rate_limit) - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.4f} seconds")
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    def query_database(
            self, 
            database_id: str, 
            filter_params: Optional[Dict] = None, 
            sorts: Optional[List[Dict]] = None,
            cache_key: Optional[str] = None, 
            cache_timeout: int = 300
        ) -> List[Dict]:
        """
        Query a Notion database with pagination, caching, and rate limiting.
        
        Args:
            database_id: The ID of the Notion database
            filter_params: Optional filter parameters
            sorts: Optional sort parameters
            cache_key: Optional cache key for storing results
            cache_timeout: Cache timeout in seconds (default: 300)
            
        Returns:
            List of database items
        """
        if not self.client:
            return []
            
        # Check cache first
        if cache_key and cache.get(cache_key):
            logger.debug(f"Cache hit for key: {cache_key}")
            return cache.get(cache_key)
        
        logger.debug(f"Querying Notion database: {database_id}")
        self._respect_rate_limit()
        
        # Prepare query parameters
        query_params = {}
        if filter_params:
            query_params['filter'] = filter_params
        if sorts:
            query_params['sorts'] = sorts
            
        # Handle pagination
        results = []
        has_more = True
        next_cursor = None
        
        while has_more:
            self._respect_rate_limit()
            
            # Add start_cursor if we have one
            if next_cursor:
                query_params['start_cursor'] = next_cursor
                
            try:
                response = self.client.databases.query(
                    database_id=database_id,
                    **query_params
                )
                
                # Add results and update pagination info
                results.extend(response.get('results', []))
                has_more = response.get('has_more', False)
                next_cursor = response.get('next_cursor')
                
                logger.debug(f"Retrieved {len(response.get('results', []))} items from Notion")
                
            except Exception as e:
                logger.error(f"Error querying Notion database: {str(e)}")
                # Implement retry logic here if needed
                raise
        
        # Cache the results if a cache key was provided
        if cache_key:
            logger.debug(f"Caching results with key: {cache_key}")
            cache.set(cache_key, results, cache_timeout)
            
        return results
    
    def get_page(self, page_id: str, cache_key: Optional[str] = None, cache_timeout: int = 300) -> Dict:
        """
        Retrieve a Notion page by ID.
        
        Args:
            page_id: The ID of the Notion page
            cache_key: Optional cache key
            cache_timeout: Cache timeout in seconds
            
        Returns:
            Page data
        """
        if not self.client:
            return {}
            
        # Check cache first
        if cache_key and cache.get(cache_key):
            return cache.get(cache_key)
        
        self._respect_rate_limit()
        
        try:
            page = self.client.pages.retrieve(page_id=page_id)
            
            # Cache the result if a cache key was provided
            if cache_key:
                cache.set(cache_key, page, cache_timeout)
                
            return page
        except Exception as e:
            logger.error(f"Error retrieving Notion page: {str(e)}")
            raise
    
    def create_page(self, database_id: str, properties: Dict) -> Dict:
        """
        Create a new page in a Notion database.
        
        Args:
            database_id: The ID of the parent database
            properties: The page properties
            
        Returns:
            Created page data
        """
        if not self.client:
            return {}
            
        self._respect_rate_limit()
        
        try:
            page = self.client.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )
            logger.info(f"Created new page in database {database_id}")
            return page
        except Exception as e:
            logger.error(f"Error creating Notion page: {str(e)}")
            raise
    
    def update_page(self, page_id: str, properties: Dict) -> Dict:
        """
        Update a Notion page.
        
        Args:
            page_id: The ID of the page to update
            properties: The updated properties
            
        Returns:
            Updated page data
        """
        if not self.client:
            return {}
            
        self._respect_rate_limit()
        
        try:
            page = self.client.pages.update(
                page_id=page_id,
                properties=properties
            )
            logger.info(f"Updated page {page_id}")
            return page
        except Exception as e:
            logger.error(f"Error updating Notion page: {str(e)}")
            raise
            
    def archive_page(self, page_id: str) -> Dict:
        """
        Archive a Notion page.
        
        Args:
            page_id: The ID of the page to archive
            
        Returns:
            Updated page data
        """
        if not self.client:
            return {}
            
        self._respect_rate_limit()
        
        try:
            page = self.client.pages.update(
                page_id=page_id,
                archived=True
            )
            logger.info(f"Archived page {page_id}")
            return page
        except Exception as e:
            logger.error(f"Error archiving Notion page: {str(e)}")
            raise
            
    # Referral Integration Methods
    def create_referral(self, referral):
        """
        Create a new referral in Notion.
        
        Args:
            referral: The Referral instance
            
        Returns:
            Notion page ID
        """
        if not self.client or not self._referral_service:
            logger.warning("Notion integration not available - skipping create_referral")
            return None
            
        return self._referral_service.create_referral(referral)
        
    def update_referral(self, referral):
        """
        Update an existing referral in Notion.
        
        Args:
            referral: The Referral instance
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client or not self._referral_service:
            logger.warning("Notion integration not available - skipping update_referral")
            return False
            
        return self._referral_service.update_referral(referral)
        
    def create_referral_update(self, update):
        """
        Create a referral update in Notion.
        
        Args:
            update: The ReferralUpdate instance
            
        Returns:
            Notion page ID
        """
        if not self.client or not self._referral_service:
            logger.warning("Notion integration not available - skipping create_referral_update")
            return None
            
        return self._referral_service.create_referral_update(update)
        
    def create_referral_document(self, document):
        """
        Record a document upload in Notion.
        
        Args:
            document: The ReferralDocument instance
            
        Returns:
            Notion page ID
        """
        if not self.client or not self._referral_service:
            logger.warning("Notion integration not available - skipping create_referral_document")
            return None
            
        return self._referral_service.create_referral_document(document)