"""
Analytics views for staff members to monitor referral trends and performance.
"""

import logging
import json
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Referral, ReferralUpdate, ReferralDocument, Agency, Service, ServiceCategory
from .staff_views import StaffRequiredMixin
from . import analytics

logger = logging.getLogger(__name__)

class StaffAnalyticsDashboardView(StaffRequiredMixin, TemplateView):
    """
    Analytics dashboard for staff members.
    """
    template_name = 'referrals/staff/analytics/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Basic stats
        context['total_referrals'] = Referral.objects.count()
        context['active_referrals'] = Referral.objects.exclude(
            status__in=['completed', 'denied', 'cancelled']
        ).count()
        context['completed_referrals'] = Referral.objects.filter(
            status='completed'
        ).count()
        
        # Referrals by status
        context['status_counts'] = analytics.get_referral_counts_by_status()
        
        # Referrals by priority
        context['priority_counts'] = analytics.get_referral_counts_by_priority()
        
        # Referrals by agency
        context['agency_data'] = analytics.get_referrals_by_agency()
        
        # Referrals by service category
        context['category_data'] = analytics.get_referrals_by_service_category()
        
        # Top services
        context['top_services'] = analytics.get_top_services()
        
        # Monthly referrals
        monthly_data = analytics.get_monthly_referrals(months=12)
        context['monthly_labels'] = json.dumps(list(monthly_data.keys()))
        context['monthly_data'] = json.dumps(list(monthly_data.values()))
        
        # Completion time stats
        context['completion_stats'] = analytics.get_completion_time_stats()
        
        # Staff performance
        context['staff_stats'] = analytics.get_staff_performance_stats()
        
        # Unassigned referrals
        context['unassigned_count'] = Referral.objects.filter(
            assigned_to__isnull=True
        ).exclude(
            status__in=['completed', 'denied', 'cancelled']
        ).count()
        
        return context

class ServiceAnalyticsView(StaffRequiredMixin, TemplateView):
    """
    Analytics specifically for services.
    """
    template_name = 'referrals/staff/analytics/services.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Service stats
        context['total_services'] = Service.objects.count()
        context['active_services'] = Service.objects.filter(is_active=True).count()
        
        # Most requested services
        context['top_services'] = analytics.get_top_services()
        
        # Services with no referrals
        context['unused_services'] = Service.objects.annotate(
            referral_count=Count('referrals')
        ).filter(
            referral_count=0
        ).values('name', 'agency__name', 'category__name')
        
        # Category distribution
        context['category_data'] = analytics.get_referrals_by_service_category()
        
        # Agency distribution
        context['agency_data'] = analytics.get_referrals_by_agency()
        
        return context

class PerformanceAnalyticsView(StaffRequiredMixin, TemplateView):
    """
    Analytics for staff performance.
    """
    template_name = 'referrals/staff/analytics/performance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Staff performance metrics
        context['staff_stats'] = analytics.get_staff_performance_stats()
        
        # Completion time stats
        context['completion_stats'] = analytics.get_completion_time_stats()
        
        # Response time stats (average time to first update after submission)
        submitted_referrals = Referral.objects.filter(
            submitted_at__isnull=False
        ).exclude(
            status='draft'
        )
        
        response_times = []
        
        for referral in submitted_referrals:
            first_update = referral.updates.exclude(
                created_by=referral.constituent
            ).order_by('created_at').first()
            
            if first_update and referral.submitted_at:
                response_time = first_update.created_at - referral.submitted_at
                response_times.append(response_time.total_seconds() / 86400)  # Days
        
        if response_times:
            context['avg_response_time'] = sum(response_times) / len(response_times)
            context['response_time_count'] = len(response_times)
        else:
            context['avg_response_time'] = None
            context['response_time_count'] = 0
        
        return context