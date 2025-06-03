"""Notion integration for document management."""
from datetime import datetime
from typing import Dict, List, Optional
from .client import NotionService
from .database import create_property, parse_property_value


# Document database schema
DOCUMENT_SCHEMA = {
    "Title": {
        "title": {}
    },
    "Description": {
        "rich_text": {}
    },
    "Category": {
        "select": {
            "options": [
                {"name": "Forms", "color": "blue"},
                {"name": "Applications", "color": "green"},
                {"name": "Legal Documents", "color": "red"},
                {"name": "ID Documents", "color": "purple"},
                {"name": "Reports", "color": "orange"},
                {"name": "Correspondence", "color": "yellow"},
                {"name": "Others", "color": "gray"}
            ]
        }
    },
    "File Type": {
        "select": {
            "options": [
                {"name": "PDF", "color": "red"},
                {"name": "DOC/DOCX", "color": "blue"},
                {"name": "JPG/PNG", "color": "green"},
                {"name": "XLSX", "color": "yellow"},
                {"name": "Other", "color": "gray"}
            ]
        }
    },
    "Status": {
        "select": {
            "options": [
                {"name": "Draft", "color": "gray"},
                {"name": "Pending Review", "color": "yellow"},
                {"name": "Approved", "color": "green"},
                {"name": "Rejected", "color": "red"},
                {"name": "Archived", "color": "purple"}
            ]
        }
    },
    "File Size": {
        "number": {
            "format": "byte"
        }
    },
    "Version": {
        "number": {}
    },
    "Uploaded By": {
        "rich_text": {}
    },
    "Upload Date": {
        "date": {}
    },
    "Constituent ID": {
        "rich_text": {}
    },
    "Referral ID": {
        "rich_text": {}
    },
    "Tags": {
        "multi_select": {
            "options": []
        }
    },
    "File URL": {
        "url": {}
    },
    "Parent Document ID": {
        "rich_text": {}
    },
    "Is Public": {
        "checkbox": {}
    }
}


def create_document_in_notion(document, notion_service: NotionService, database_id: str):
    """Create a document record in Notion."""
    properties = {
        "Title": create_property("title", document.title),
        "Description": create_property("rich_text", document.description),
        "Category": create_property("select", document.category.name if document.category else "Others"),
        "File Type": create_property("select", document.file_type.upper() if document.file_type else "Other"),
        "Status": create_property("select", dict(document.DOCUMENT_STATUS).get(document.status, document.status)),
        "File Size": create_property("number", document.file_size),
        "Version": create_property("number", document.version),
        "Uploaded By": create_property("rich_text", document.uploaded_by.get_full_name() if document.uploaded_by else ""),
        "Upload Date": create_property("date", document.created_at.isoformat()),
        "Is Public": create_property("checkbox", document.is_public),
    }
    
    # Add optional fields
    if document.constituent:
        properties["Constituent ID"] = create_property("rich_text", str(document.constituent.id))
    
    if document.referral:
        properties["Referral ID"] = create_property("rich_text", str(document.referral.id))
    
    if document.tags:
        tag_list = [tag.strip() for tag in document.tags.split(',')]
        properties["Tags"] = create_property("multi_select", tag_list)
    
    if document.file:
        # For file URL, you'd typically upload to cloud storage and store the URL
        properties["File URL"] = create_property("url", document.file.url if hasattr(document.file, 'url') else "")
    
    if document.parent_document:
        properties["Parent Document ID"] = create_property("rich_text", str(document.parent_document.id))
    
    result = notion_service.create_page(database_id, properties)
    return result


def update_document_in_notion(document, notion_service: NotionService):
    """Update a document record in Notion."""
    if not document.notion_id:
        return None
    
    properties = {
        "Title": create_property("title", document.title),
        "Description": create_property("rich_text", document.description),
        "Category": create_property("select", document.category.name if document.category else "Others"),
        "Status": create_property("select", dict(document.DOCUMENT_STATUS).get(document.status, document.status)),
        "Version": create_property("number", document.version),
        "Is Public": create_property("checkbox", document.is_public),
    }
    
    if document.tags:
        tag_list = [tag.strip() for tag in document.tags.split(',')]
        properties["Tags"] = create_property("multi_select", tag_list)
    
    result = notion_service.update_page(document.notion_id, properties)
    return result


def get_document_from_notion(notion_id: str, notion_service: NotionService):
    """Get a document from Notion by ID."""
    page = notion_service.get_page(notion_id)
    return parse_document_from_notion(page)


def parse_document_from_notion(page: Dict) -> Dict:
    """Parse a Notion page into document data."""
    properties = page.get("properties", {})
    
    return {
        "notion_id": page["id"],
        "title": parse_property_value(properties.get("Title", {})),
        "description": parse_property_value(properties.get("Description", {})),
        "category": parse_property_value(properties.get("Category", {})),
        "file_type": parse_property_value(properties.get("File Type", {})),
        "status": parse_property_value(properties.get("Status", {})),
        "file_size": parse_property_value(properties.get("File Size", {})),
        "version": parse_property_value(properties.get("Version", {})),
        "uploaded_by": parse_property_value(properties.get("Uploaded By", {})),
        "upload_date": parse_property_value(properties.get("Upload Date", {})),
        "constituent_id": parse_property_value(properties.get("Constituent ID", {})),
        "referral_id": parse_property_value(properties.get("Referral ID", {})),
        "tags": parse_property_value(properties.get("Tags", {})),
        "file_url": parse_property_value(properties.get("File URL", {})),
        "parent_document_id": parse_property_value(properties.get("Parent Document ID", {})),
        "is_public": parse_property_value(properties.get("Is Public", {})),
    }


def search_documents_in_notion(notion_service: NotionService, database_id: str, 
                             filters: Optional[Dict] = None) -> List[Dict]:
    """Search for documents in Notion with optional filters."""
    filter_obj = {"and": []}
    
    if filters:
        if filters.get("category"):
            filter_obj["and"].append({
                "property": "Category",
                "select": {"equals": filters["category"]}
            })
        
        if filters.get("status"):
            filter_obj["and"].append({
                "property": "Status",
                "select": {"equals": filters["status"]}
            })
        
        if filters.get("constituent_id"):
            filter_obj["and"].append({
                "property": "Constituent ID",
                "rich_text": {"equals": filters["constituent_id"]}
            })
        
        if filters.get("referral_id"):
            filter_obj["and"].append({
                "property": "Referral ID",
                "rich_text": {"equals": filters["referral_id"]}
            })
    
    results = notion_service.query_database(
        database_id, 
        filter=filter_obj if filter_obj["and"] else None,
        sorts=[{"property": "Upload Date", "direction": "descending"}]
    )
    
    documents = []
    for page in results:
        documents.append(parse_document_from_notion(page))
    
    return documents