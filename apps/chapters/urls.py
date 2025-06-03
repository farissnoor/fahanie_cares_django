from django.urls import path
from . import views

urlpatterns = [
    # Public views
    path('', views.ChapterListView.as_view(), name='chapter_list'),
    path('<slug:slug>/', views.ChapterDetailView.as_view(), name='chapter_detail'),
    path('<slug:slug>/join/', views.MembershipApplicationView.as_view(), name='chapter_join'),
    path('<slug:slug>/members/', views.ChapterMembershipView.as_view(), name='chapter_members'),
    
    # Activities
    path('<slug:slug>/activities/', views.ChapterActivityListView.as_view(), name='chapter_activities'),
    path('activity/<int:pk>/', views.ChapterActivityDetailView.as_view(), name='activity_detail'),
    path('activity/<int:pk>/register/', views.ActivityRegistrationView.as_view(), name='activity_register'),
    
    # Management (coordinators and staff)
    path('<slug:slug>/dashboard/', views.ChapterDashboardView.as_view(), name='chapter_dashboard'),
    path('<slug:slug>/edit/', views.ChapterUpdateView.as_view(), name='chapter_edit'),
    
    # Staff only
    path('create/', views.ChapterCreateView.as_view(), name='chapter_create'),
    
    # Activity management
    path('<slug:slug>/activities/create/', views.ChapterCreateView.as_view(), name='activity_create'),
]