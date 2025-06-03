from django.urls import path
from . import views
from .member_views import (
    FahanieCaresMemberRegistrationView, 
    RegistrationSuccessView,
    MemberProfileView,
    MemberUpdateView,
    MemberListView,
    MemberDetailView,
    MemberCreateView
)

urlpatterns = [
    # Member Registration URLs
    path('member/register/', FahanieCaresMemberRegistrationView.as_view(), name='member_register'),
    path('member/register/success/', RegistrationSuccessView.as_view(), name='registration_success'),
    path('member/profile/', MemberProfileView.as_view(), name='member_profile'),
    path('member/profile/update/', MemberUpdateView.as_view(), name='member_update'),
    path('staff/members/', MemberListView.as_view(), name='staff_member_list'),
    path('staff/members/create/', MemberCreateView.as_view(), name='member_create'),
    path('staff/members/<int:pk>/', MemberDetailView.as_view(), name='member_detail'),
    
    # Staff Constituent URLs
    path('staff/constituents/', views.StaffConstituentDashboardView.as_view(), name='staff_constituent_dashboard'),
    path('staff/constituents/<int:pk>/', views.StaffConstituentDetailView.as_view(), name='staff_constituent_detail'),
    path('staff/constituents/create/', views.StaffConstituentCreateView.as_view(), name='staff_constituent_create'),
    path('staff/constituents/<int:pk>/update/', views.StaffConstituentUpdateView.as_view(), name='staff_constituent_update'),
    
    # Constituent Interaction URLs
    path('staff/constituents/<int:constituent_id>/interactions/create/', views.StaffConstituentInteractionCreateView.as_view(), name='staff_constituent_interaction_create'),
    
    # Constituent Group URLs
    path('staff/constituent-groups/', views.StaffConstituentGroupListView.as_view(), name='staff_constituent_group_list'),
    path('staff/constituent-groups/<slug:slug>/', views.StaffConstituentGroupDetailView.as_view(), name='staff_constituent_group_detail'),
    path('staff/constituent-groups/create/', views.StaffConstituentGroupCreateView.as_view(), name='staff_constituent_group_create'),
    path('staff/constituent-groups/<slug:slug>/update/', views.StaffConstituentGroupUpdateView.as_view(), name='staff_constituent_group_update'),
    
    # Analytics
    path('staff/constituents/analytics/', views.StaffConstituentAnalyticsView.as_view(), name='staff_constituent_analytics'),
]