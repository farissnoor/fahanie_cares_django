from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Count, Q, Avg, Sum
from typing import Dict, List, Optional, Any
from utils.notion.client import NotionService
from apps.referrals.models import Referral, ReferralUpdate
from apps.constituents.models import Constituent, ConstituentInteraction
from apps.chapters.models import Chapter
from apps.documents.models import Document
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for generating analytics and reports."""
    
    def __init__(self, notion_service: NotionService = None):
        self.notion_service = notion_service or NotionService()
    
    def get_dashboard_metrics(self, start_date: datetime = None, end_date: datetime = None) -> Dict:
        """Get comprehensive dashboard metrics."""
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        metrics = {
            'referrals': self.get_referral_metrics(start_date, end_date),
            'constituents': self.get_constituent_metrics(start_date, end_date),
            'chapters': self.get_chapter_metrics(),
            'geographic': self.get_geographic_distribution(),
            'trends': self.get_trend_data(start_date, end_date),
        }
        
        return metrics
    
    def get_referral_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get referral analytics."""
        referrals = Referral.objects.filter(
            created_at__range=(start_date, end_date)
        )
        
        total_referrals = referrals.count()
        
        status_counts = referrals.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        category_counts = referrals.values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        priority_counts = referrals.values('priority').annotate(
            count=Count('id')
        ).order_by('priority')
        
        # Average resolution time
        completed_referrals = referrals.filter(status='completed')
        if completed_referrals.exists():
            avg_resolution_time = sum([
                (r.updated_at - r.created_at).days
                for r in completed_referrals
            ]) / completed_referrals.count()
        else:
            avg_resolution_time = 0
        
        # Monthly trend
        monthly_trend = referrals.extra(
            select={'month': "date_format(created_at, '%%Y-%%m')"}
        ).values('month').annotate(count=Count('id')).order_by('month')
        
        return {
            'total': total_referrals,
            'status_counts': {item['status']: item['count'] for item in status_counts},
            'category_counts': {item['category__name']: item['count'] for item in category_counts},
            'priority_counts': {item['priority']: item['count'] for item in priority_counts},
            'avg_resolution_time': avg_resolution_time,
            'monthly_trend': list(monthly_trend),
            'completion_rate': (completed_referrals.count() / total_referrals * 100) if total_referrals > 0 else 0,
        }
    
    def get_constituent_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get constituent analytics."""
        constituents = Constituent.objects.filter(
            created_at__range=(start_date, end_date)
        )
        
        total_constituents = Constituent.objects.count()
        new_constituents = constituents.count()
        
        # Active constituents (those with recent interactions)
        active_constituents = Constituent.objects.filter(
            interactions__created_at__range=(start_date, end_date)
        ).distinct().count()
        
        # Chapter membership
        chapter_members = Constituent.objects.filter(
            chapter_membership__is_active=True
        ).count()
        
        # Geographic distribution
        municipality_counts = Constituent.objects.values('municipality').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Age distribution
        age_groups = {
            '18-25': constituents.filter(age__range=(18, 25)).count(),
            '26-35': constituents.filter(age__range=(26, 35)).count(),
            '36-45': constituents.filter(age__range=(36, 45)).count(),
            '46-55': constituents.filter(age__range=(46, 55)).count(),
            '56-65': constituents.filter(age__range=(56, 65)).count(),
            '65+': constituents.filter(age__gte=65).count(),
        }
        
        # Interaction types
        interaction_counts = ConstituentInteraction.objects.filter(
            created_at__range=(start_date, end_date)
        ).values('interaction_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'total': total_constituents,
            'new': new_constituents,
            'active': active_constituents,
            'chapter_members': chapter_members,
            'municipality_distribution': {item['municipality']: item['count'] for item in municipality_counts},
            'age_groups': age_groups,
            'interaction_types': {item['interaction_type']: item['count'] for item in interaction_counts},
            'engagement_rate': (active_constituents / total_constituents * 100) if total_constituents > 0 else 0,
        }
    
    def get_chapter_metrics(self) -> Dict:
        """Get chapter analytics."""
        chapters = Chapter.objects.all()
        
        total_chapters = chapters.count()
        active_chapters = chapters.filter(is_active=True).count()
        
        # Member counts by chapter
        chapter_member_counts = []
        for chapter in chapters:
            member_count = chapter.members.filter(is_active=True).count()
            chapter_member_counts.append({
                'name': chapter.name,
                'members': member_count,
                'location': chapter.location,
                'is_active': chapter.is_active,
            })
        
        # Sort by member count
        chapter_member_counts.sort(key=lambda x: x['members'], reverse=True)
        
        # Activity metrics
        total_events = sum(chapter.events.count() for chapter in chapters)
        total_meetings = sum(chapter.meetings.count() for chapter in chapters)
        
        return {
            'total': total_chapters,
            'active': active_chapters,
            'chapter_details': chapter_member_counts[:10],  # Top 10 chapters
            'total_members': sum(ch['members'] for ch in chapter_member_counts),
            'total_events': total_events,
            'total_meetings': total_meetings,
            'avg_members_per_chapter': sum(ch['members'] for ch in chapter_member_counts) / total_chapters if total_chapters > 0 else 0,
        }
    
    def get_geographic_distribution(self) -> Dict:
        """Get geographic distribution of constituents and services."""
        # Constituent distribution
        constituent_distribution = Constituent.objects.values('municipality').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Referral distribution
        referral_distribution = Referral.objects.values('constituent__municipality').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Combine data
        geographic_data = {}
        
        for item in constituent_distribution:
            municipality = item['municipality'] or 'Unknown'
            geographic_data[municipality] = {
                'constituents': item['count'],
                'referrals': 0,
            }
        
        for item in referral_distribution:
            municipality = item['constituent__municipality'] or 'Unknown'
            if municipality in geographic_data:
                geographic_data[municipality]['referrals'] = item['count']
            else:
                geographic_data[municipality] = {
                    'constituents': 0,
                    'referrals': item['count'],
                }
        
        return geographic_data
    
    def get_trend_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get trend data for various metrics."""
        # Daily referrals
        referral_trend = []
        constituent_trend = []
        
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)
            
            # Referrals for this day
            daily_referrals = Referral.objects.filter(
                created_at__range=(current_date, next_date)
            ).count()
            
            # New constituents for this day
            daily_constituents = Constituent.objects.filter(
                created_at__range=(current_date, next_date)
            ).count()
            
            referral_trend.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': daily_referrals,
            })
            
            constituent_trend.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': daily_constituents,
            })
            
            current_date = next_date
        
        return {
            'referrals': referral_trend,
            'constituents': constituent_trend,
        }
    
    def generate_custom_report(self, report_type: str, start_date: datetime = None, 
                             end_date: datetime = None, filters: Dict = None) -> Dict:
        """Generate custom report based on type and filters."""
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        if report_type == 'referrals':
            return self._generate_referral_report(start_date, end_date, filters)
        elif report_type == 'constituents':
            return self._generate_constituent_report(start_date, end_date, filters)
        elif report_type == 'chapters':
            return self._generate_chapter_report(filters)
        elif report_type == 'services':
            return self._generate_service_report(start_date, end_date, filters)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
    
    def _generate_referral_report(self, start_date: datetime, end_date: datetime, 
                                 filters: Dict = None) -> Dict:
        """Generate detailed referral report."""
        query = Referral.objects.filter(created_at__range=(start_date, end_date))
        
        # Apply filters
        if filters:
            if filters.get('status'):
                query = query.filter(status=filters['status'])
            if filters.get('category'):
                query = query.filter(category__id=filters['category'])
            if filters.get('priority'):
                query = query.filter(priority=filters['priority'])
            if filters.get('municipality'):
                query = query.filter(constituent__municipality=filters['municipality'])
        
        # Get data
        referrals = query.select_related('constituent', 'category').order_by('-created_at')
        
        # Prepare report data
        report_data = []
        for referral in referrals:
            report_data.append({
                'reference_number': referral.reference_number,
                'constituent': referral.constituent.name,
                'category': referral.category.name,
                'status': referral.status,
                'priority': referral.priority,
                'created_at': referral.created_at,
                'updated_at': referral.updated_at,
                'description': referral.description,
                'notes': referral.notes,
            })
        
        # Summary statistics
        summary = {
            'total': query.count(),
            'by_status': dict(query.values('status').annotate(count=Count('id')).values_list('status', 'count')),
            'by_priority': dict(query.values('priority').annotate(count=Count('id')).values_list('priority', 'count')),
            'by_category': dict(query.values('category__name').annotate(count=Count('id')).values_list('category__name', 'count')),
        }
        
        return {
            'data': report_data,
            'summary': summary,
            'filters': filters,
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
            },
        }
    
    def _generate_constituent_report(self, start_date: datetime, end_date: datetime, 
                                    filters: Dict = None) -> Dict:
        """Generate detailed constituent report."""
        query = Constituent.objects.all()
        
        # Apply filters
        if filters:
            if filters.get('municipality'):
                query = query.filter(municipality=filters['municipality'])
            if filters.get('barangay'):
                query = query.filter(barangay=filters['barangay'])
            if filters.get('chapter_member'):
                query = query.filter(chapter_membership__is_active=True)
            if filters.get('age_min'):
                query = query.filter(age__gte=filters['age_min'])
            if filters.get('age_max'):
                query = query.filter(age__lte=filters['age_max'])
        
        # Filter by registration date if specified
        if filters and filters.get('registration_period'):
            query = query.filter(created_at__range=(start_date, end_date))
        
        constituents = query.order_by('name')
        
        # Prepare report data
        report_data = []
        for constituent in constituents:
            report_data.append({
                'name': constituent.name,
                'municipality': constituent.municipality,
                'barangay': constituent.barangay,
                'contact_number': constituent.contact_number,
                'email': constituent.email,
                'age': constituent.age,
                'chapter_member': constituent.chapter_membership.filter(is_active=True).exists(),
                'referral_count': constituent.referrals.count(),
                'last_interaction': constituent.interactions.order_by('-created_at').first(),
                'created_at': constituent.created_at,
            })
        
        # Summary statistics
        summary = {
            'total': query.count(),
            'by_municipality': dict(query.values('municipality').annotate(count=Count('id')).values_list('municipality', 'count')),
            'by_barangay': dict(query.values('barangay').annotate(count=Count('id')).values_list('barangay', 'count')),
            'chapter_members': query.filter(chapter_membership__is_active=True).count(),
            'avg_age': query.aggregate(avg_age=Avg('age'))['avg_age'],
            'with_referrals': query.filter(referrals__isnull=False).distinct().count(),
        }
        
        return {
            'data': report_data,
            'summary': summary,
            'filters': filters,
        }
    
    def _generate_chapter_report(self, filters: Dict = None) -> Dict:
        """Generate detailed chapter report."""
        query = Chapter.objects.all()
        
        # Apply filters
        if filters:
            if filters.get('is_active'):
                query = query.filter(is_active=True)
            if filters.get('location'):
                query = query.filter(location__icontains=filters['location'])
        
        chapters = query.prefetch_related('members', 'events', 'meetings')
        
        # Prepare report data
        report_data = []
        for chapter in chapters:
            report_data.append({
                'name': chapter.name,
                'location': chapter.location,
                'is_active': chapter.is_active,
                'member_count': chapter.members.filter(is_active=True).count(),
                'total_events': chapter.events.count(),
                'total_meetings': chapter.meetings.count(),
                'recent_events': list(chapter.events.order_by('-date')[:5].values(
                    'title', 'date', 'attendee_count'
                )),
                'created_at': chapter.created_at,
            })
        
        # Summary statistics
        total_chapters = query.count()
        active_chapters = query.filter(is_active=True).count()
        total_members = sum(ch['member_count'] for ch in report_data)
        
        summary = {
            'total_chapters': total_chapters,
            'active_chapters': active_chapters,
            'total_members': total_members,
            'avg_members_per_chapter': total_members / total_chapters if total_chapters > 0 else 0,
            'total_events': sum(ch['total_events'] for ch in report_data),
            'total_meetings': sum(ch['total_meetings'] for ch in report_data),
        }
        
        return {
            'data': report_data,
            'summary': summary,
            'filters': filters,
        }
    
    def _generate_service_report(self, start_date: datetime, end_date: datetime, 
                                filters: Dict = None) -> Dict:
        """Generate service delivery report."""
        # Get referrals grouped by service/category
        query = Referral.objects.filter(created_at__range=(start_date, end_date))
        
        if filters:
            if filters.get('category'):
                query = query.filter(category__id=filters['category'])
            if filters.get('status'):
                query = query.filter(status=filters['status'])
        
        # Service delivery by category
        category_stats = query.values('category__name').annotate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            pending=Count('id', filter=Q(status='pending')),
            processing=Count('id', filter=Q(status='processing')),
        ).order_by('-total')
        
        # Service delivery timeline
        timeline = []
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=7)  # Weekly buckets
            week_referrals = query.filter(created_at__range=(current_date, next_date))
            
            timeline.append({
                'week_start': current_date.strftime('%Y-%m-%d'),
                'total': week_referrals.count(),
                'completed': week_referrals.filter(status='completed').count(),
            })
            
            current_date = next_date
        
        # Average processing time by category
        processing_times = {}
        for category in category_stats:
            category_name = category['category__name']
            completed_referrals = query.filter(
                category__name=category_name,
                status='completed'
            )
            
            if completed_referrals.exists():
                avg_time = sum([
                    (r.updated_at - r.created_at).days
                    for r in completed_referrals
                ]) / completed_referrals.count()
                processing_times[category_name] = avg_time
        
        return {
            'category_stats': list(category_stats),
            'timeline': timeline,
            'processing_times': processing_times,
            'summary': {
                'total_services': query.count(),
                'completed': query.filter(status='completed').count(),
                'completion_rate': (query.filter(status='completed').count() / query.count() * 100) if query.count() > 0 else 0,
            },
            'filters': filters,
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
            },
        }