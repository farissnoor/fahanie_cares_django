"""
Notion integration service for Staff Management.
Handles synchronization between Django Staff models and Notion Staff Profiles database.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, date
from django.conf import settings
from .client import NotionService

logger = logging.getLogger(__name__)

class StaffNotionService(NotionService):
    """
    Service for managing staff data in Notion.
    """
    
    def __init__(self, token=None):
        super().__init__(token)
        # Get the staff database ID from settings
        self.staff_database_id = getattr(settings, 'NOTION_STAFF_DATABASE', '1c304d49-511d-804e-9f8a-d0853ff01ea1')
        
    def get_all_staff(self, cache_timeout: int = 300) -> List[Dict]:
        """
        Retrieve all staff members from Notion.
        
        Returns:
            List of staff records from Notion
        """
        cache_key = 'notion_staff_all'
        return self.query_database(
            database_id=self.staff_database_id,
            cache_key=cache_key,
            cache_timeout=cache_timeout
        )
    
    def get_staff_by_division(self, division: str, cache_timeout: int = 300) -> List[Dict]:
        """
        Get staff members by division.
        
        Args:
            division: The division to filter by
            cache_timeout: Cache timeout in seconds
            
        Returns:
            List of staff records from the specified division
        """
        filter_params = {
            "property": "Division",
            "select": {
                "equals": division
            }
        }
        
        cache_key = f'notion_staff_division_{division}'
        return self.query_database(
            database_id=self.staff_database_id,
            filter_params=filter_params,
            cache_key=cache_key,
            cache_timeout=cache_timeout
        )
    
    def get_staff_by_employment_status(self, status: str, cache_timeout: int = 300) -> List[Dict]:
        """
        Get staff members by employment status.
        
        Args:
            status: The employment status to filter by
            cache_timeout: Cache timeout in seconds
            
        Returns:
            List of staff records with the specified employment status
        """
        filter_params = {
            "property": "Employment Status",
            "select": {
                "equals": status
            }
        }
        
        cache_key = f'notion_staff_status_{status}'
        return self.query_database(
            database_id=self.staff_database_id,
            filter_params=filter_params,
            cache_key=cache_key,
            cache_timeout=cache_timeout
        )
    
    def sync_staff_from_notion(self) -> List[Dict]:
        """
        Synchronize Django Staff models with Notion data.
        
        Returns:
            List of staff records that were processed
        """
        staff_records = self.get_all_staff()
        
        # Import here to avoid circular imports
        from apps.staff.models import Staff
        
        synced_staff = []
        
        for record in staff_records:
            try:
                staff_data = self._parse_notion_staff_record(record)
                
                # Get or create staff member
                staff, created = Staff.objects.get_or_create(
                    notion_id=record['id'],
                    defaults=staff_data
                )
                
                # Update existing staff with new data
                if not created:
                    for field, value in staff_data.items():
                        setattr(staff, field, value)
                    staff.save()
                
                synced_staff.append({
                    'staff': staff,
                    'created': created,
                    'notion_record': record
                })
                
                logger.info(f"{'Created' if created else 'Updated'} staff: {staff.full_name}")
                
            except Exception as e:
                logger.error(f"Error syncing staff record {record.get('id', 'unknown')}: {str(e)}")
                continue
        
        return synced_staff
    
    def _parse_notion_staff_record(self, record: Dict) -> Dict:
        """
        Parse a Notion staff record into Django model fields.
        
        Args:
            record: Notion page record
            
        Returns:
            Dictionary of fields for Django Staff model
        """
        properties = record.get('properties', {})
        
        # Helper function to get text from rich_text property
        def get_rich_text(prop_name: str) -> str:
            prop = properties.get(prop_name, {})
            if prop.get('type') == 'rich_text' and prop.get('rich_text'):
                return '\n'.join([rt.get('plain_text', '') for rt in prop['rich_text']])
            return ''
        
        # Helper function to get title text
        def get_title_text(prop_name: str) -> str:
            prop = properties.get(prop_name, {})
            if prop.get('type') == 'title' and prop.get('title'):
                return '\n'.join([t.get('plain_text', '') for t in prop['title']])
            return ''
        
        # Helper function to get select value
        def get_select_value(prop_name: str) -> str:
            prop = properties.get(prop_name, {})
            if prop.get('type') == 'select' and prop.get('select'):
                return prop['select'].get('name', '')
            return ''
        
        # Helper function to get email
        def get_email(prop_name: str) -> str:
            prop = properties.get(prop_name, {})
            if prop.get('type') == 'email':
                return prop.get('email', '')
            return ''
        
        # Helper function to get phone number
        def get_phone(prop_name: str) -> str:
            prop = properties.get(prop_name, {})
            if prop.get('type') == 'phone_number':
                return prop.get('phone_number', '')
            return ''
        
        # Helper function to get date
        def get_date(prop_name: str) -> Optional[date]:
            prop = properties.get(prop_name, {})
            if prop.get('type') == 'date' and prop.get('date'):
                date_str = prop['date'].get('start')
                if date_str:
                    try:
                        return datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        pass
            return None
        
        # Map Notion values to Django choices
        division_mapping = {
            'Legislative Affairs': 'legislative_affairs',
            'Administrative Affairs': 'administrative_affairs',
            'Communications': 'communications',
            "MP Uy-Oyod's Office": 'mp_office',
            'IT Unit': 'it_unit',
        }
        
        employment_status_mapping = {
            'Coterminous': 'coterminous',
            'Contractual': 'contractual',
            'Consultant': 'consultant',
            'Intern': 'intern',
            'Volunteer': 'volunteer',
        }
        
        office_mapping = {
            'Main Office': 'main_office',
            'Satellite Office': 'satellite_office',
        }
        
        # Extract data
        full_name = get_title_text('Full Name')
        position = get_rich_text('Position/Designation')
        email = get_email('Email Address')
        phone_number = get_phone('Phone Number')
        address = get_rich_text('Address')
        
        # Get mapped values
        division_notion = get_select_value('Division')
        division = division_mapping.get(division_notion, '')
        
        employment_status_notion = get_select_value('Employment Status')
        employment_status = employment_status_mapping.get(employment_status_notion, '')
        
        office_notion = get_select_value('Office')
        office = office_mapping.get(office_notion, '')
        
        date_hired = get_date('Date Hired/Engaged')
        duties_responsibilities = get_rich_text('Duties and Responsibilities')
        staff_workflow = get_rich_text('Staff Workflow')
        
        return {
            'full_name': full_name,
            'position': position,
            'email': email,
            'phone_number': phone_number,
            'address': address,
            'division': division,
            'office': office,
            'employment_status': employment_status,
            'date_hired': date_hired,
            'duties_responsibilities': duties_responsibilities,
            'staff_workflow': staff_workflow,
            'is_active': True,  # Default to active
        }
    
    def create_staff_in_notion(self, staff) -> Optional[str]:
        """
        Create a new staff member in Notion.
        
        Args:
            staff: Django Staff model instance
            
        Returns:
            Notion page ID if successful, None otherwise
        """
        try:
            properties = self._staff_to_notion_properties(staff)
            
            response = self.create_page(
                database_id=self.staff_database_id,
                properties=properties
            )
            
            notion_id = response.get('id')
            if notion_id:
                # Update the staff record with the Notion ID
                staff.notion_id = notion_id
                staff.save()
                logger.info(f"Created staff in Notion: {staff.full_name} ({notion_id})")
            
            return notion_id
            
        except Exception as e:
            logger.error(f"Error creating staff in Notion: {str(e)}")
            return None
    
    def update_staff_in_notion(self, staff) -> bool:
        """
        Update an existing staff member in Notion.
        
        Args:
            staff: Django Staff model instance
            
        Returns:
            True if successful, False otherwise
        """
        if not staff.notion_id:
            logger.warning(f"Staff {staff.full_name} has no Notion ID - cannot update")
            return False
        
        try:
            properties = self._staff_to_notion_properties(staff)
            
            self.update_page(
                page_id=staff.notion_id,
                properties=properties
            )
            
            logger.info(f"Updated staff in Notion: {staff.full_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating staff in Notion: {str(e)}")
            return False
    
    def _staff_to_notion_properties(self, staff) -> Dict:
        """
        Convert Django Staff model to Notion page properties.
        
        Args:
            staff: Django Staff model instance
            
        Returns:
            Dictionary of Notion properties
        """
        # Reverse mapping for choices
        division_reverse_mapping = {
            'legislative_affairs': 'Legislative Affairs',
            'administrative_affairs': 'Administrative Affairs',
            'communications': 'Communications',
            'mp_office': "MP Uy-Oyod's Office",
            'it_unit': 'IT Unit',
        }
        
        employment_status_reverse_mapping = {
            'coterminous': 'Coterminous',
            'contractual': 'Contractual',
            'consultant': 'Consultant',
            'intern': 'Intern',
            'volunteer': 'Volunteer',
        }
        
        office_reverse_mapping = {
            'main_office': 'Main Office',
            'satellite_office': 'Satellite Office',
        }
        
        properties = {
            'Full Name': {
                'title': [
                    {
                        'type': 'text',
                        'text': {'content': staff.full_name}
                    }
                ]
            }
        }
        
        # Add optional properties if they exist
        if staff.position:
            properties['Position/Designation'] = {
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {'content': staff.position}
                    }
                ]
            }
        
        if staff.email:
            properties['Email Address'] = {'email': staff.email}
        
        if staff.phone_number:
            properties['Phone Number'] = {'phone_number': staff.phone_number}
        
        if staff.address:
            properties['Address'] = {
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {'content': staff.address}
                    }
                ]
            }
        
        if staff.division:
            notion_division = division_reverse_mapping.get(staff.division)
            if notion_division:
                properties['Division'] = {
                    'select': {'name': notion_division}
                }
        
        if staff.employment_status:
            notion_status = employment_status_reverse_mapping.get(staff.employment_status)
            if notion_status:
                properties['Employment Status'] = {
                    'select': {'name': notion_status}
                }
        
        if staff.office:
            notion_office = office_reverse_mapping.get(staff.office)
            if notion_office:
                properties['Office'] = {
                    'select': {'name': notion_office}
                }
        
        if staff.date_hired:
            properties['Date Hired/Engaged'] = {
                'date': {'start': staff.date_hired.isoformat()}
            }
        
        if staff.duties_responsibilities:
            properties['Duties and Responsibilities'] = {
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {'content': staff.duties_responsibilities}
                    }
                ]
            }
        
        if staff.staff_workflow:
            properties['Staff Workflow'] = {
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {'content': staff.staff_workflow}
                    }
                ]
            }
        
        return properties