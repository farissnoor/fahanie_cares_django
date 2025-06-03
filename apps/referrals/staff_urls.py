from django.urls import path
from . import staff_views
from . import staff_analytics_views

urlpatterns = [
    # Staff Dashboard
    path('', staff_views.StaffDashboardView.as_view(), name='staff_dashboard'),
    
    # Analytics (must come before dynamic referral URLs)
    path('analytics/', staff_analytics_views.StaffAnalyticsDashboardView.as_view(), name='staff_analytics_dashboard'),
    path('analytics/services/', staff_analytics_views.ServiceAnalyticsView.as_view(), name='staff_analytics_services'),
    path('analytics/performance/', staff_analytics_views.PerformanceAnalyticsView.as_view(), name='staff_analytics_performance'),
    
    # Referral Management (dynamic URLs come last)
    path('<str:reference_number>/', staff_views.StaffReferralDetailView.as_view(), name='staff_referral_detail'),
    path('<str:reference_number>/update/', staff_views.StaffReferralUpdateView.as_view(), name='staff_referral_update'),
    path('<str:reference_number>/add-status/', staff_views.StaffReferralUpdateCreateView.as_view(), name='staff_referral_update_create'),
    path('<str:reference_number>/upload-document/', staff_views.StaffDocumentUploadView.as_view(), name='staff_document_upload'),
    path('<str:reference_number>/assign-to-me/', staff_views.AssignToMeView.as_view(), name='staff_assign_to_me'),
]