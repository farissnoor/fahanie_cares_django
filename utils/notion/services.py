"""
Notion integration for Service Programs.
"""
from .client import NotionService
from .database import (
    create_database_schema,
    map_notion_to_django,
    map_django_to_notion
)
from apps.services.models import ServiceProgram, ServiceApplication, ServiceDisbursement

# Service Catalog Database Schema
SERVICE_CATALOG_SCHEMA = {
    "Service Name": {"type": "title", "name": "Service Name"},
    "Category": {"type": "select", "name": "Category"},
    "Status": {"type": "select", "name": "Status"},
    "Description": {"type": "rich_text", "name": "Description"},
    "Objectives": {"type": "rich_text", "name": "Objectives"},
    "Eligibility Criteria": {"type": "rich_text", "name": "Eligibility Criteria"},
    "Required Documents": {"type": "rich_text", "name": "Required Documents"},
    "Target Beneficiaries": {"type": "rich_text", "name": "Target Beneficiaries"},
    "Start Date": {"type": "date", "name": "Start Date"},
    "End Date": {"type": "date", "name": "End Date"},
    "Application Start": {"type": "date", "name": "Application Start"},
    "Application End": {"type": "date", "name": "Application End"},
    "Capacity": {"type": "number", "name": "Capacity"},
    "Current Beneficiaries": {"type": "number", "name": "Current Beneficiaries"},
    "Budget Allocation": {"type": "number", "name": "Budget Allocation"},
    "Budget Utilized": {"type": "number", "name": "Budget Utilized"},
    "Partner Agencies": {"type": "rich_text", "name": "Partner Agencies"},
    "Resources": {"type": "files", "name": "Resources"},
    "Application Form": {"type": "files", "name": "Application Form"}
}

# Service Application Database Schema
SERVICE_APPLICATION_SCHEMA = {
    "Application ID": {"type": "title", "name": "Application ID"},
    "Service": {"type": "relation", "name": "Service"},
    "Applicant": {"type": "relation", "name": "Applicant"},
    "Date Applied": {"type": "date", "name": "Date Applied"},
    "Status": {"type": "select", "name": "Status"},
    "Priority Level": {"type": "select", "name": "Priority Level"},
    "Documents": {"type": "files", "name": "Documents"},
    "Appointment Date": {"type": "date", "name": "Appointment Date"},
    "Reason for Application": {"type": "rich_text", "name": "Reason for Application"},
    "Supporting Details": {"type": "rich_text", "name": "Supporting Details"},
    "Assessment Notes": {"type": "rich_text", "name": "Assessment Notes"},
    "Assigned Staff": {"type": "relation", "name": "Assigned Staff"},
    "Assistance Amount": {"type": "number", "name": "Assistance Amount"},
    "Assistance Description": {"type": "rich_text", "name": "Assistance Description"},
    "Disbursement Date": {"type": "date", "name": "Disbursement Date"},
    "Outcome": {"type": "rich_text", "name": "Outcome"}
}

def create_service_program_in_notion(program: ServiceProgram, notion_service: NotionService, database_id: str):
    """Create a service program record in Notion."""
    properties = {
        "Service Name": {"title": [{"text": {"content": program.name}}]},
        "Category": {"select": {"name": program.get_program_type_display()}},
        "Status": {"select": {"name": program.get_status_display()}},
        "Description": {"rich_text": [{"text": {"content": program.description}}]},
        "Objectives": {"rich_text": [{"text": {"content": program.objectives}}]},
        "Eligibility Criteria": {"rich_text": [{"text": {"content": program.eligibility_criteria}}]},
        "Required Documents": {"rich_text": [{"text": {"content": program.required_documents}}]},
        "Target Beneficiaries": {"rich_text": [{"text": {"content": program.target_beneficiaries}}]},
        "Start Date": {"date": {"start": str(program.start_date)}},
        "Capacity": {"number": program.max_beneficiaries},
        "Current Beneficiaries": {"number": program.beneficiary_count},
        "Budget Allocation": {"number": float(program.total_budget)},
        "Budget Utilized": {"number": float(program.budget_utilized)}
    }
    
    if program.end_date:
        properties["End Date"] = {"date": {"start": str(program.end_date)}}
    
    if program.application_start:
        properties["Application Start"] = {"date": {"start": str(program.application_start)}}
    
    if program.application_end:
        properties["Application End"] = {"date": {"start": str(program.application_end)}}
    
    if program.partner_agencies:
        properties["Partner Agencies"] = {"rich_text": [{"text": {"content": program.partner_agencies}}]}
    
    result = notion_service.create_page(
        parent_database_id=database_id,
        properties=properties
    )
    
    # Update program with Notion ID
    program.notion_id = result['id']
    program.save(update_fields=['notion_id'])
    
    return result

def create_service_application_in_notion(application: ServiceApplication, notion_service: NotionService, database_id: str):
    """Create a service application in Notion."""
    properties = {
        "Application ID": {"title": [{"text": {"content": application.application_number}}]},
        "Date Applied": {"date": {"start": str(application.created_at.date())}},
        "Status": {"select": {"name": application.get_status_display()}},
        "Priority Level": {"select": {"name": application.get_priority_level_display()}},
        "Reason for Application": {"rich_text": [{"text": {"content": application.reason_for_application}}]}
    }
    
    # Add relations if Notion IDs exist
    if application.program.notion_id:
        properties["Service"] = {"relation": [{"id": application.program.notion_id}]}
    
    if hasattr(application.applicant, 'constituent_profile') and application.applicant.constituent_profile.notion_id:
        properties["Applicant"] = {"relation": [{"id": application.applicant.constituent_profile.notion_id}]}
    
    if application.supporting_details:
        properties["Supporting Details"] = {"rich_text": [{"text": {"content": application.supporting_details}}]}
    
    if application.assessment_notes:
        properties["Assessment Notes"] = {"rich_text": [{"text": {"content": application.assessment_notes}}]}
    
    if application.assistance_amount:
        properties["Assistance Amount"] = {"number": float(application.assistance_amount)}
    
    if application.assistance_description:
        properties["Assistance Description"] = {"rich_text": [{"text": {"content": application.assistance_description}}]}
    
    if application.disbursement_date:
        properties["Disbursement Date"] = {"date": {"start": str(application.disbursement_date)}}
    
    result = notion_service.create_page(
        parent_database_id=database_id,
        properties=properties
    )
    
    # Update application with Notion ID
    application.notion_id = result['id']
    application.save(update_fields=['notion_id'])
    
    return result

def update_service_application_in_notion(application: ServiceApplication, notion_service: NotionService):
    """Update a service application in Notion."""
    if not application.notion_id:
        return None
    
    properties = {
        "Status": {"select": {"name": application.get_status_display()}},
        "Priority Level": {"select": {"name": application.get_priority_level_display()}}
    }
    
    if application.assessment_notes:
        properties["Assessment Notes"] = {"rich_text": [{"text": {"content": application.assessment_notes}}]}
    
    if application.assistance_amount:
        properties["Assistance Amount"] = {"number": float(application.assistance_amount)}
    
    if application.assistance_description:
        properties["Assistance Description"] = {"rich_text": [{"text": {"content": application.assistance_description}}]}
    
    return notion_service.update_page(
        page_id=application.notion_id,
        properties=properties
    )

def sync_service_metrics_to_notion(program: ServiceProgram, notion_service: NotionService):
    """Sync service program metrics to Notion."""
    if not program.notion_id:
        return None
    
    properties = {
        "Current Beneficiaries": {"number": program.beneficiary_count},
        "Budget Utilized": {"number": float(program.budget_utilized)},
        "Status": {"select": {"name": program.get_status_display()}}
    }
    
    return notion_service.update_page(
        page_id=program.notion_id,
        properties=properties
    )

def get_service_availability(program: ServiceProgram):
    """Check service availability and return details."""
    availability = {
        'is_open': program.is_accepting_applications(),
        'capacity': program.max_beneficiaries,
        'current_beneficiaries': program.beneficiary_count,
        'available_slots': max(0, program.max_beneficiaries - program.beneficiary_count),
        'application_deadline': program.application_end,
        'budget_remaining': float(program.total_budget - program.budget_utilized)
    }
    
    # Check if service is at capacity
    if availability['available_slots'] == 0:
        availability['is_open'] = False
        availability['reason'] = 'Service has reached maximum capacity'
    
    # Check application period
    elif program.application_end and program.application_end < timezone.now().date():
        availability['is_open'] = False
        availability['reason'] = 'Application period has ended'
    
    # Check budget availability
    elif availability['budget_remaining'] <= 0:
        availability['is_open'] = False
        availability['reason'] = 'Budget has been exhausted'
    
    return availability

def generate_application_id(program: ServiceProgram):
    """Generate a unique application ID."""
    import time
    import random
    
    prefix = f"APP-{program.slug[:3].upper()}"
    timestamp = str(int(time.time()))[-6:]
    random_num = random.randint(100, 999)
    
    return f"{prefix}-{timestamp}-{random_num}"