"""
Notion integration for Chapter Management.
"""
from .client import NotionService
from .database import (
    create_database_schema,
    map_notion_to_django,
    map_django_to_notion
)
from apps.chapters.models import Chapter, ChapterMembership, ChapterActivity

# Chapter Database Schema
CHAPTER_SCHEMA = {
    "Chapter Name": {"type": "title", "name": "Chapter Name"},
    "Municipality": {"type": "select", "name": "Municipality"},
    "Province": {"type": "select", "name": "Province"},
    "Tier": {"type": "select", "name": "Tier"},
    "Coordinator": {"type": "relation", "name": "Coordinator"},
    "Members": {"type": "relation", "name": "Members"},
    "Establishment Date": {"type": "date", "name": "Establishment Date"},
    "Status": {"type": "select", "name": "Status"},
    "Meeting Schedule": {"type": "rich_text", "name": "Meeting Schedule"},
    "Description": {"type": "rich_text", "name": "Description"},
    "Goals": {"type": "rich_text", "name": "Goals"},
    "Resources": {"type": "files", "name": "Resources"},
    "Performance Metrics": {"type": "rich_text", "name": "Performance Metrics"},
    "Member Count": {"type": "number", "name": "Member Count"},
    "Volunteer Count": {"type": "number", "name": "Volunteer Count"},
    "Activity Count": {"type": "number", "name": "Activity Count"}
}

# Chapter Event Database Schema
CHAPTER_EVENT_SCHEMA = {
    "Event Name": {"type": "title", "name": "Event Name"},
    "Chapter": {"type": "relation", "name": "Chapter"},
    "Date": {"type": "date", "name": "Date"},
    "Start Time": {"type": "rich_text", "name": "Start Time"},
    "End Time": {"type": "rich_text", "name": "End Time"},
    "Location": {"type": "rich_text", "name": "Location"},
    "Description": {"type": "rich_text", "name": "Description"},
    "Attendees": {"type": "relation", "name": "Attendees"},
    "Volunteers": {"type": "relation", "name": "Volunteers"},
    "Resources Needed": {"type": "rich_text", "name": "Resources Needed"},
    "Status": {"type": "select", "name": "Status"},
    "Outcome": {"type": "rich_text", "name": "Outcome"},
    "Photos": {"type": "files", "name": "Photos"},
    "Target Participants": {"type": "number", "name": "Target Participants"},
    "Actual Participants": {"type": "number", "name": "Actual Participants"},
    "Budget": {"type": "number", "name": "Budget"},
    "Actual Cost": {"type": "number", "name": "Actual Cost"}
}

def create_chapter_in_notion(chapter: Chapter, notion_service: NotionService, database_id: str):
    """Create a chapter record in Notion."""
    properties = {
        "Chapter Name": {"title": [{"text": {"content": chapter.name}}]},
        "Municipality": {"select": {"name": chapter.municipality}},
        "Tier": {"select": {"name": chapter.get_tier_display()}},
        "Status": {"select": {"name": chapter.get_status_display()}},
        "Member Count": {"number": chapter.member_count},
        "Volunteer Count": {"number": chapter.volunteer_count},
        "Activity Count": {"number": chapter.activity_count}
    }
    
    if chapter.province:
        properties["Province"] = {"select": {"name": chapter.province}}
    
    if chapter.established_date:
        properties["Establishment Date"] = {"date": {"start": str(chapter.established_date)}}
    
    if chapter.description:
        properties["Description"] = {"rich_text": [{"text": {"content": chapter.description}}]}
    
    if chapter.meeting_schedule:
        properties["Meeting Schedule"] = {"rich_text": [{"text": {"content": chapter.meeting_schedule}}]}
    
    if chapter.mission_statement:
        properties["Goals"] = {"rich_text": [{"text": {"content": chapter.mission_statement}}]}
    
    result = notion_service.create_page(
        parent_database_id=database_id,
        properties=properties
    )
    
    # Update chapter with Notion ID
    chapter.notion_id = result['id']
    chapter.save(update_fields=['notion_id'])
    
    return result

def update_chapter_in_notion(chapter: Chapter, notion_service: NotionService):
    """Update a chapter record in Notion."""
    if not chapter.notion_id:
        return None
    
    properties = {
        "Chapter Name": {"title": [{"text": {"content": chapter.name}}]},
        "Municipality": {"select": {"name": chapter.municipality}},
        "Status": {"select": {"name": chapter.get_status_display()}},
        "Member Count": {"number": chapter.member_count},
        "Volunteer Count": {"number": chapter.volunteer_count},
        "Activity Count": {"number": chapter.activity_count}
    }
    
    return notion_service.update_page(
        page_id=chapter.notion_id,
        properties=properties
    )

def create_activity_in_notion(activity: ChapterActivity, notion_service: NotionService, database_id: str):
    """Create a chapter activity in Notion."""
    properties = {
        "Event Name": {"title": [{"text": {"content": activity.title}}]},
        "Date": {"date": {"start": str(activity.date)}},
        "Start Time": {"rich_text": [{"text": {"content": str(activity.start_time)}}]},
        "End Time": {"rich_text": [{"text": {"content": str(activity.end_time)}}]},
        "Location": {"rich_text": [{"text": {"content": activity.venue}}]},
        "Description": {"rich_text": [{"text": {"content": activity.description}}]},
        "Status": {"select": {"name": activity.get_status_display()}},
        "Target Participants": {"number": activity.target_participants},
        "Actual Participants": {"number": activity.actual_participants},
        "Budget": {"number": float(activity.budget)},
        "Actual Cost": {"number": float(activity.actual_cost)}
    }
    
    if activity.chapter.notion_id:
        properties["Chapter"] = {"relation": [{"id": activity.chapter.notion_id}]}
    
    if activity.objectives:
        properties["Resources Needed"] = {"rich_text": [{"text": {"content": activity.objectives}}]}
    
    if activity.report:
        properties["Outcome"] = {"rich_text": [{"text": {"content": activity.report}}]}
    
    result = notion_service.create_page(
        parent_database_id=database_id,
        properties=properties
    )
    
    # Update activity with Notion ID
    activity.notion_id = result['id']
    activity.save(update_fields=['notion_id'])
    
    return result

def sync_chapter_members_to_notion(chapter: Chapter, notion_service: NotionService):
    """Sync chapter members to Notion."""
    if not chapter.notion_id:
        return None
    
    # Get active member IDs
    member_ids = []
    memberships = ChapterMembership.objects.filter(
        chapter=chapter,
        status='active'
    ).select_related('user')
    
    for membership in memberships:
        # Assuming user profiles have notion_id
        if hasattr(membership.user, 'constituent_profile') and membership.user.constituent_profile.notion_id:
            member_ids.append({"id": membership.user.constituent_profile.notion_id})
    
    # Update chapter with member relations
    properties = {
        "Members": {"relation": member_ids}
    }
    
    return notion_service.update_page(
        page_id=chapter.notion_id,
        properties=properties
    )

def get_chapter_performance_metrics(chapter: Chapter):
    """Calculate and return chapter performance metrics."""
    from django.db.models import Count, Sum, Avg
    from datetime import datetime, timedelta
    
    now = datetime.now()
    last_month = now - timedelta(days=30)
    last_quarter = now - timedelta(days=90)
    
    metrics = {
        'member_growth': {
            'monthly': ChapterMembership.objects.filter(
                chapter=chapter,
                created_at__gte=last_month
            ).count(),
            'quarterly': ChapterMembership.objects.filter(
                chapter=chapter,
                created_at__gte=last_quarter
            ).count()
        },
        'activity_metrics': {
            'monthly_count': ChapterActivity.objects.filter(
                chapter=chapter,
                date__gte=last_month.date()
            ).count(),
            'quarterly_count': ChapterActivity.objects.filter(
                chapter=chapter,
                date__gte=last_quarter.date()
            ).count(),
            'avg_attendance': ChapterActivity.objects.filter(
                chapter=chapter,
                status='completed'
            ).aggregate(avg=Avg('actual_participants'))['avg'] or 0
        },
        'volunteer_metrics': {
            'active_volunteers': ChapterMembership.objects.filter(
                chapter=chapter,
                is_volunteer=True,
                status='active'
            ).count(),
            'total_hours': ChapterMembership.objects.filter(
                chapter=chapter,
                is_volunteer=True
            ).aggregate(total=Sum('volunteer_hours'))['total'] or 0
        },
        'engagement_metrics': {
            'member_participation_rate': 0,  # Calculate based on activity attendance
            'volunteer_conversion_rate': 0,  # Calculate based on members becoming volunteers
        }
    }
    
    # Calculate participation rate
    total_members = chapter.member_count
    if total_members > 0:
        active_participants = ChapterMembership.objects.filter(
            chapter=chapter,
            status='active',
            activities_attended__gt=0
        ).count()
        metrics['engagement_metrics']['member_participation_rate'] = (active_participants / total_members) * 100
    
    # Calculate volunteer conversion rate
    if total_members > 0:
        volunteer_count = metrics['volunteer_metrics']['active_volunteers']
        metrics['engagement_metrics']['volunteer_conversion_rate'] = (volunteer_count / total_members) * 100
    
    return metrics