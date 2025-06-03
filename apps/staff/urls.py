from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Dashboard
    path('', views.staff_dashboard, name='dashboard'),
    
    # Staff Profile (Personal)
    path('profile/', views.staff_profile, name='profile'),
    path('profile/edit/', views.edit_staff_profile, name='edit_profile'),
    path('directory/', views.staff_directory, name='directory'),
    
    # Staff Management
    path('list/', views.StaffListView.as_view(), name='staff_list'),
    path('staff/<int:pk>/', views.StaffDetailView.as_view(), name='staff_detail'),
    
    # Teams
    path('teams/', views.StaffTeamListView.as_view(), name='team_list'),
    path('teams/<int:pk>/', views.StaffTeamDetailView.as_view(), name='team_detail'),
    
    # Attendance
    path('attendance/', views.attendance_tracking, name='attendance_tracking'),
    path('attendance/report/', views.attendance_report, name='attendance_report'),
    
    # Performance
    path('performance/', views.staff_performance_overview, name='performance_overview'),
    
    # Notion Integration
    path('sync/', views.sync_from_notion, name='sync_from_notion'),
    
    # Export
    path('export/csv/', views.export_staff_csv, name='export_staff_csv'),
]