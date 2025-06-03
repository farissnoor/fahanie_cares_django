"""
Notion database utilities for #FahanieCares.
Contains functions for working with Notion databases, including mapping between
Django and Notion data structures.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

logger = logging.getLogger(__name__)

def format_title(text: str) -> Dict:
    """
    Format a string as a Notion title property.
    
    Args:
        text: The text for the title
        
    Returns:
        Formatted title property
    """
    return {
        'title': [
            {
                'text': {
                    'content': text
                }
            }
        ]
    }

def format_rich_text(text: str) -> Dict:
    """
    Format a string as a Notion rich text property.
    
    Args:
        text: The text content
        
    Returns:
        Formatted rich text property
    """
    return {
        'rich_text': [
            {
                'text': {
                    'content': text
                }
            }
        ]
    }

def create_database_schema(name: str, properties: Dict) -> Dict:
    """
    Create a Notion database schema.
    
    Args:
        name: The database name
        properties: The property schema
        
    Returns:
        Formatted database schema
    """
    return {
        'object': 'database',
        'title': [
            {
                'text': {
                    'content': name
                }
            }
        ],
        'properties': properties
    }

def map_notion_to_django(page: Dict) -> Dict:
    """
    Map Notion page data to Django model fields.
    
    Args:
        page: The Notion page object
        
    Returns:
        Django model fields
    """
    props = page.get('properties', {})
    
    # Extract values based on property types
    def extract_value(prop: Dict) -> Any:
        prop_type = prop.get('type')
        
        if prop_type == 'title':
            return prop.get('title', [{}])[0].get('plain_text', '')
        elif prop_type == 'rich_text':
            return prop.get('rich_text', [{}])[0].get('plain_text', '')
        elif prop_type == 'select':
            select = prop.get('select')
            return select.get('name', '') if select else ''
        elif prop_type == 'multi_select':
            return [item.get('name', '') for item in prop.get('multi_select', [])]
        elif prop_type == 'date':
            date = prop.get('date')
            return date.get('start') if date else None
        elif prop_type == 'number':
            return prop.get('number')
        elif prop_type == 'checkbox':
            return prop.get('checkbox', False)
        elif prop_type == 'url':
            return prop.get('url', '')
        elif prop_type == 'email':
            return prop.get('email', '')
        elif prop_type == 'phone_number':
            return prop.get('phone_number', '')
        elif prop_type == 'people':
            return [person.get('id') for person in prop.get('people', [])]
        elif prop_type == 'relation':
            return [rel.get('id') for rel in prop.get('relation', [])]
        else:
            return None
    
    # Map properties to Django fields
    django_data = {
        'notion_id': page.get('id'),
        'url': page.get('url'),
        'created_time': page.get('created_time'),
        'last_edited_time': page.get('last_edited_time'),
        'archived': page.get('archived', False),
    }
    
    # Process all properties
    for prop_name, prop_value in props.items():
        # Convert property names to lowercase and replace spaces with underscores
        field_name = prop_name.lower().replace(' ', '_')
        django_data[field_name] = extract_value(prop_value)
    
    return django_data

def map_django_to_notion(model_instance) -> Dict:
    """
    Map Django model fields to Notion properties.
    
    Args:
        model_instance: The Django model instance
        
    Returns:
        Notion properties
    """
    # Create base properties dict
    properties = {}
    
    # Map common fields
    for field in model_instance._meta.get_fields():
        field_name = field.name
        value = getattr(model_instance, field_name, None)
        
        if value is not None:
            # Convert field name to title case
            prop_name = field_name.replace('_', ' ').title()
            
            # Map to appropriate Notion property type
            if isinstance(value, str):
                if field_name == 'title' or field_name == 'name':
                    properties[prop_name] = format_title(value)
                else:
                    properties[prop_name] = format_rich_text(value)
            elif isinstance(value, bool):
                properties[prop_name] = format_checkbox(value)
            elif isinstance(value, (int, float)):
                properties[prop_name] = format_number(value)
            elif isinstance(value, datetime):
                properties[prop_name] = format_date(value.isoformat())
            elif isinstance(value, list):
                properties[prop_name] = format_multi_select(value)
    
    return properties

def format_select(option: str) -> Dict:
    """
    Format a string as a Notion select property.
    
    Args:
        option: The selected option
        
    Returns:
        Formatted select property
    """
    return {
        'select': {
            'name': option
        }
    }

def format_multi_select(options: List[str]) -> Dict:
    """
    Format a list of strings as a Notion multi-select property.
    
    Args:
        options: List of selected options
        
    Returns:
        Formatted multi-select property
    """
    return {
        'multi_select': [
            {'name': option} for option in options
        ]
    }

def format_date(date_str: str) -> Dict:
    """
    Format a date string as a Notion date property.
    
    Args:
        date_str: ISO format date string
        
    Returns:
        Formatted date property
    """
    return {
        'date': {
            'start': date_str
        }
    }

def format_number(number: Union[int, float]) -> Dict:
    """
    Format a number as a Notion number property.
    
    Args:
        number: The numeric value
        
    Returns:
        Formatted number property
    """
    return {
        'number': number
    }

def format_checkbox(checked: bool) -> Dict:
    """
    Format a boolean as a Notion checkbox property.
    
    Args:
        checked: Whether the checkbox is checked
        
    Returns:
        Formatted checkbox property
    """
    return {
        'checkbox': checked
    }

def format_email(email: str) -> Dict:
    """
    Format a string as a Notion email property.
    
    Args:
        email: The email address
        
    Returns:
        Formatted email property
    """
    return {
        'email': email
    }

def format_phone_number(phone: str) -> Dict:
    """
    Format a string as a Notion phone number property.
    
    Args:
        phone: The phone number
        
    Returns:
        Formatted phone number property
    """
    return {
        'phone_number': phone
    }

def format_url(url: str) -> Dict:
    """
    Format a string as a Notion URL property.
    
    Args:
        url: The URL
        
    Returns:
        Formatted URL property
    """
    return {
        'url': url
    }

def format_people(user_ids: List[str]) -> Dict:
    """
    Format a list of user IDs as a Notion people property.
    
    Args:
        user_ids: List of Notion user IDs
        
    Returns:
        Formatted people property
    """
    return {
        'people': [
            {'id': user_id} for user_id in user_ids
        ]
    }

def format_relation(page_ids: List[str]) -> Dict:
    """
    Format a list of page IDs as a Notion relation property.
    
    Args:
        page_ids: List of Notion page IDs
        
    Returns:
        Formatted relation property
    """
    return {
        'relation': [
            {'id': page_id} for page_id in page_ids
        ]
    }

def create_property(prop_type: str, name: str, **kwargs) -> Dict:
    """
    Create a Notion property definition.
    
    Args:
        prop_type: The property type
        name: The property name
        **kwargs: Additional property configuration
        
    Returns:
        Property definition
    """
    property_def = {
        'type': prop_type,
        'name': name
    }
    
    # Add type-specific configuration
    if prop_type == 'select' and 'options' in kwargs:
        property_def['select'] = {
            'options': [{'name': opt, 'color': 'default'} for opt in kwargs['options']]
        }
    elif prop_type == 'multi_select' and 'options' in kwargs:
        property_def['multi_select'] = {
            'options': [{'name': opt, 'color': 'default'} for opt in kwargs['options']]
        }
    elif prop_type == 'relation' and 'database_id' in kwargs:
        property_def['relation'] = {
            'database_id': kwargs['database_id'],
            'single_property': kwargs.get('single_property', True)
        }
    
    return property_def

def parse_property_value(prop_value: Dict, prop_type: str) -> Any:
    """
    Parse a Notion property value.
    
    Args:
        prop_value: The property value from Notion
        prop_type: The property type
        
    Returns:
        Parsed value
    """
    if prop_type == 'title':
        return prop_value.get('title', [{}])[0].get('plain_text', '')
    elif prop_type == 'rich_text':
        return prop_value.get('rich_text', [{}])[0].get('plain_text', '')
    elif prop_type == 'select':
        select = prop_value.get('select')
        return select.get('name', '') if select else ''
    elif prop_type == 'multi_select':
        return [item.get('name', '') for item in prop_value.get('multi_select', [])]
    elif prop_type == 'date':
        date = prop_value.get('date')
        return date.get('start') if date else None
    elif prop_type == 'number':
        return prop_value.get('number')
    elif prop_type == 'checkbox':
        return prop_value.get('checkbox', False)
    elif prop_type == 'url':
        return prop_value.get('url', '')
    elif prop_type == 'email':
        return prop_value.get('email', '')
    elif prop_type == 'phone_number':
        return prop_value.get('phone_number', '')
    elif prop_type == 'people':
        return [person.get('id') for person in prop_value.get('people', [])]
    elif prop_type == 'relation':
        return [rel.get('id') for rel in prop_value.get('relation', [])]
    else:
        return None