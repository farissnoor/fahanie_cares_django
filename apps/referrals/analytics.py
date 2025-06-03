"""
Analytics utilities for the Referrals module.
Provides functions for aggregating and analyzing referral data.
"""

import logging
from datetime import datetime, timedelta
from django.db.models import Count, Q, Avg, ExpressionWrapper, F, fields
from django.db.models.functions import ExtractMonth, ExtractYear, TruncMonth, TruncDate, TruncWeek
from django.utils import timezone

from .models import Referral, ReferralUpdate, ReferralDocument, Service, ServiceCategory, Agency

logger = logging.getLogger(__name__)

def get_referral_counts_by_status():
    """Get counts of referrals by status."""
    return {
        status[0]: Referral.objects.filter(status=status[0]).count()
        for status in Referral.STATUS_CHOICES
    }

def get_referral_counts_by_priority():
    """Get counts of referrals by priority."""
    return {
        priority[0]: Referral.objects.filter(priority=priority[0]).count()
        for priority in Referral.PRIORITY_CHOICES
    }

def get_referrals_by_agency():
    """Get counts of referrals by agency."""
    return (Agency.objects
        .annotate(referral_count=Count('services__referrals'))
        .filter(referral_count__gt=0)
        .order_by('-referral_count')
        .values('name', 'referral_count')
    )

def get_referrals_by_service_category():
    """Get counts of referrals by service category."""
    return (ServiceCategory.objects
        .annotate(referral_count=Count('services__referrals'))
        .filter(referral_count__gt=0)
        .order_by('-referral_count')
        .values('name', 'referral_count')
    )

def get_top_services():
    """Get top 10 most requested services."""
    return (Service.objects
        .annotate(referral_count=Count('referrals'))
        .filter(referral_count__gt=0)
        .order_by('-referral_count')
        .values('name', 'referral_count', 'agency__name')[:10]
    )

def get_monthly_referrals(months=12):
    """Get referral counts by month for the last N months."""
    end_date = timezone.now().date().replace(day=1)
    start_date = (end_date - timedelta(days=30*months)).replace(day=1)
    
    # Get monthly counts
    monthly_data = (Referral.objects
        .filter(created_at__gte=start_date)
        .annotate(
            month=TruncMonth('created_at'),
        )
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    # Convert to dictionary with formatted dates
    return {
        item['month'].strftime('%b %Y'): item['count']
        for item in monthly_data
    }

def get_completion_time_stats():
    """Get average time to complete referrals by service category."""
    # Calculate time difference for completed referrals
    completed_referrals = Referral.objects.filter(
        status='completed',
        submitted_at__isnull=False,
        completed_at__isnull=False
    )
    
    # Calculate overall average in days
    overall_avg = None
    if completed_referrals.exists():
        time_diff = ExpressionWrapper(
            F('completed_at') - F('submitted_at'),
            output_field=fields.DurationField()
        )
        overall_avg = completed_referrals.annotate(
            time_diff=time_diff
        ).aggregate(
            avg_days=Avg(time_diff)
        )['avg_days']
        
        if overall_avg:
            overall_avg = overall_avg.total_seconds() / 86400  # Convert to days
    
    # Get averages by category
    category_data = []
    for category in ServiceCategory.objects.filter(services__referrals__status='completed').distinct():
        category_referrals = completed_referrals.filter(service__category=category)
        if category_referrals.exists():
            time_diff = ExpressionWrapper(
                F('completed_at') - F('submitted_at'),
                output_field=fields.DurationField()
            )
            avg_days = category_referrals.annotate(
                time_diff=time_diff
            ).aggregate(
                avg_days=Avg(time_diff)
            )['avg_days']
            
            if avg_days:
                category_data.append({
                    'name': category.name,
                    'avg_days': avg_days.total_seconds() / 86400  # Convert to days
                })
    
    return {
        'overall_avg_days': overall_avg,
        'by_category': sorted(category_data, key=lambda x: x['avg_days'])
    }

def get_staff_performance_stats():
    """Get stats on staff performance with referrals."""
    from apps.users.models import User
    
    staff_users = User.objects.filter(user_type__in=['staff', 'mp'])
    staff_stats = []
    
    for user in staff_users:
        # Assigned referrals
        assigned_count = Referral.objects.filter(assigned_to=user).count()
        
        # Completed referrals
        completed_count = Referral.objects.filter(
            assigned_to=user,
            status='completed'
        ).count()
        
        # Active referrals (not completed or denied)
        active_count = Referral.objects.filter(
            assigned_to=user
        ).exclude(
            status__in=['completed', 'denied', 'cancelled']
        ).count()
        
        # Calculate average completion time
        avg_completion_days = None
        completed_referrals = Referral.objects.filter(
            assigned_to=user,
            status='completed',
            submitted_at__isnull=False,
            completed_at__isnull=False
        )
        
        if completed_referrals.exists():
            time_diff = ExpressionWrapper(
                F('completed_at') - F('submitted_at'),
                output_field=fields.DurationField()
            )
            avg_completion = completed_referrals.annotate(
                time_diff=time_diff
            ).aggregate(
                avg_days=Avg(time_diff)
            )['avg_days']
            
            if avg_completion:
                avg_completion_days = avg_completion.total_seconds() / 86400
        
        # Add to results if they've had at least one assigned referral
        if assigned_count > 0:
            staff_stats.append({
                'name': user.get_full_name(),
                'assigned_count': assigned_count,
                'completed_count': completed_count,
                'active_count': active_count,
                'completion_rate': (completed_count / assigned_count * 100) if assigned_count else 0,
                'avg_completion_days': avg_completion_days
            })
    
    return sorted(staff_stats, key=lambda x: x['assigned_count'], reverse=True)