"""
Notion integration for the Referrals module of #FahanieCares.
Maps referral records to Notion database and implements CRUD operations.
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from django.conf import settings

from .client import NotionService
from .database import (
    format_title, format_rich_text, format_select, 
    format_date, format_relation, format_checkbox,
    format_phone_number, format_email, format_url
)

logger = logging.getLogger(__name__)

class ReferralNotionService:
    """
    Service for managing referrals in Notion.
    """
    def __init__(self, token=None):
        """
        Initialize the service with the Notion client.
        """
        self.notion = NotionService(token)
        self.referrals_db_id = getattr(settings, 'NOTION_REFERRALS_DB_ID', '')
        self.services_db_id = getattr(settings, 'NOTION_SERVICES_DB_ID', '')
        self.agencies_db_id = getattr(settings, 'NOTION_AGENCIES_DB_ID', '')
        self.users_db_id = getattr(settings, 'NOTION_USERS_DB_ID', '')
        
    def map_referral_to_notion(self, referral) -> Dict:
        """
        Map a Django Referral model to Notion properties.
        
        Args:
            referral: The Referral instance to map
            
        Returns:
            Dict of Notion properties
        """
        properties = {
            "Reference Number": format_title(referral.reference_number),
            "Status": format_select(referral.status),
            "Priority": format_select(referral.priority),
            "Description": format_rich_text(referral.description),
            "Created At": format_date(referral.created_at),
            "Updated At": format_date(referral.updated_at),
        }
        
        # Add optional fields if they exist
        if referral.supporting_documents:
            properties["Supporting Documents"] = format_rich_text(referral.supporting_documents)
            
        if referral.staff_notes:
            properties["Staff Notes"] = format_rich_text(referral.staff_notes)
            
        if referral.agency_notes:
            properties["Agency Notes"] = format_rich_text(referral.agency_notes)
            
        if referral.agency_contact:
            properties["Agency Contact"] = format_rich_text(referral.agency_contact)
            
        if referral.agency_reference:
            properties["Agency Reference"] = format_rich_text(referral.agency_reference)
            
        if referral.submitted_at:
            properties["Submitted At"] = format_date(referral.submitted_at)
            
        if referral.referred_at:
            properties["Referred At"] = format_date(referral.referred_at)
            
        if referral.completed_at:
            properties["Completed At"] = format_date(referral.completed_at)
        
        if referral.follow_up_date:
            properties["Follow Up Date"] = format_date(referral.follow_up_date)
            
        # Service information
        if referral.service and referral.service.notion_id:
            properties["Service"] = format_relation([referral.service.notion_id])
        
        # Constituent information
        if referral.constituent:
            properties["Constituent Name"] = format_rich_text(referral.constituent.get_full_name())
            
            if referral.constituent.email:
                properties["Constituent Email"] = format_email(referral.constituent.email)
                
            if hasattr(referral.constituent, 'phone_number') and referral.constituent.phone_number:
                properties["Constituent Phone"] = format_phone_number(referral.constituent.phone_number)
                
            # If user has a Notion ID, create relation
            if hasattr(referral.constituent, 'notion_id') and referral.constituent.notion_id:
                properties["Constituent"] = format_relation([referral.constituent.notion_id])
        
        # Assigned staff information
        if referral.assigned_to:
            properties["Assigned To"] = format_rich_text(referral.assigned_to.get_full_name())
            
            # If assigned user has a Notion ID, create relation
            if hasattr(referral.assigned_to, 'notion_id') and referral.assigned_to.notion_id:
                properties["Assigned Staff"] = format_relation([referral.assigned_to.notion_id])
        
        return properties
    
    def create_referral(self, referral) -> str:
        """
        Create a new referral in the Notion database.
        
        Args:
            referral: The Referral instance to create
            
        Returns:
            Notion page ID for the created referral
        """
        if not self.referrals_db_id:
            logger.error("Notion referrals database ID not configured")
            return None
        
        try:
            properties = self.map_referral_to_notion(referral)
            
            # Create the page in Notion
            response = self.notion.create_page(
                database_id=self.referrals_db_id,
                properties=properties
            )
            
            page_id = response.get('id')
            
            # Update the referral with the Notion ID
            if page_id:
                referral.notion_id = page_id
                referral.save(update_fields=['notion_id'])
                
                logger.info(f"Created referral in Notion: {referral.reference_number} -> {page_id}")
                return page_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating referral in Notion: {str(e)}")
            return None
    
    def update_referral(self, referral) -> bool:
        """
        Update an existing referral in the Notion database.
        
        Args:
            referral: The Referral instance to update
            
        Returns:
            True if the update was successful, False otherwise
        """
        if not referral.notion_id:
            # If the referral doesn't have a Notion ID, create it instead
            logger.info(f"Referral {referral.reference_number} has no Notion ID, creating instead of updating")
            return bool(self.create_referral(referral))
        
        try:
            properties = self.map_referral_to_notion(referral)
            
            # Update the page in Notion
            self.notion.update_page(
                page_id=referral.notion_id,
                properties=properties
            )
            
            logger.info(f"Updated referral in Notion: {referral.reference_number} -> {referral.notion_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating referral in Notion: {str(e)}")
            return False
    
    def create_referral_update(self, update) -> str:
        """
        Create a referral update in Notion.
        
        Args:
            update: The ReferralUpdate instance
            
        Returns:
            Notion page ID for the created update
        """
        if not self.referrals_db_id or not update.referral.notion_id:
            return None
        
        try:
            # Create a child page for the update
            properties = {
                "Title": format_title(f"Update for {update.referral.reference_number}"),
                "Status": format_select(update.status),
                "Notes": format_rich_text(update.notes),
                "Created At": format_date(update.created_at),
                "By": format_rich_text(update.created_by.get_full_name()),
            }
            
            # Add relations if the referral has a Notion ID
            if update.referral.notion_id:
                properties["Referral"] = format_relation([update.referral.notion_id])
            
            # Create the page in Notion
            response = self.notion.create_page(
                database_id=self.referrals_db_id,
                properties=properties
            )
            
            page_id = response.get('id')
            
            # Update the update with the Notion ID
            if page_id:
                update.notion_id = page_id
                update.save(update_fields=['notion_id'])
                
                logger.info(f"Created referral update in Notion: {update.id} -> {page_id}")
                return page_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating referral update in Notion: {str(e)}")
            return None
    
    def create_referral_document(self, document) -> str:
        """
        Record a document upload in Notion.
        
        Args:
            document: The ReferralDocument instance
            
        Returns:
            Notion page ID for the created document record
        """
        if not self.referrals_db_id or not document.referral.notion_id:
            return None
        
        try:
            # Create a child page for the document record
            properties = {
                "Title": format_title(document.name),
                "Created At": format_date(document.created_at),
                "Uploaded By": format_rich_text(document.uploaded_by.get_full_name()),
            }
            
            # Add file URL if available
            if document.file and hasattr(document.file, 'url'):
                properties["File URL"] = format_url(document.file.url)
            
            # Add relations if the referral has a Notion ID
            if document.referral.notion_id:
                properties["Referral"] = format_relation([document.referral.notion_id])
            
            # Create the page in Notion
            response = self.notion.create_page(
                database_id=self.referrals_db_id,
                properties=properties
            )
            
            page_id = response.get('id')
            
            # Update the document with the Notion ID
            if page_id:
                document.notion_id = page_id
                document.save(update_fields=['notion_id'])
                
                logger.info(f"Created document record in Notion: {document.id} -> {page_id}")
                return page_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating document record in Notion: {str(e)}")
            return None