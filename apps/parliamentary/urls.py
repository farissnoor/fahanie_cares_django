from django.urls import path
from . import views

app_name = 'parliamentary'

urlpatterns = [
    # Dashboard
    path('', views.ParliamentaryDashboardView.as_view(), name='dashboard'),
    
    # Legislative Measures
    path('measures/', views.LegislativeMeasureListView.as_view(), name='measure_list'),
    path('measures/create/', views.LegislativeMeasureCreateView.as_view(), name='measure_create'),
    path('measures/<int:pk>/', views.LegislativeMeasureDetailView.as_view(), name='measure_detail'),
    path('measures/<int:measure_id>/record-action/', views.record_action, name='record_action'),
    path('measures/<int:measure_id>/record-vote/', views.record_vote, name='record_vote'),
    
    # Committees
    path('committees/', views.CommitteeListView.as_view(), name='committee_list'),
    path('committees/<int:pk>/', views.CommitteeDetailView.as_view(), name='committee_detail'),
    
    # Committee Hearings
    path('hearings/<int:pk>/', views.CommitteeHearingDetailView.as_view(), name='hearing_detail'),
    
    # Oversight Activities
    path('oversight/', views.OversightActivityListView.as_view(), name='oversight_list'),
    path('oversight/<int:pk>/', views.OversightActivityDetailView.as_view(), name='oversight_detail'),
    
    # Plenary Sessions
    path('plenary/', views.PlenarySessionListView.as_view(), name='plenary_list'),
    
    # Speeches
    path('speeches/', views.SpeechPrivilegeListView.as_view(), name='speech_list'),
]