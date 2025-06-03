from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    # Public views
    path('', views.ServiceProgramListView.as_view(), name='service_program_list'),
    path('program/<slug:slug>/', views.ServiceProgramDetailView.as_view(), name='service_program_detail'),
    
    # Application views
    path('program/<slug:slug>/apply/', views.ServiceApplicationCreateView.as_view(), name='service_apply'),
    path('applications/', views.ServiceApplicationListView.as_view(), name='service_applications'),
    path('application/<int:pk>/', views.ServiceApplicationDetailView.as_view(), name='service_application_detail'),
    
    # Staff views
    path('staff/dashboard/', views.ServiceProgramDashboardView.as_view(), name='service_dashboard'),
    path('staff/applications/', views.StaffApplicationListView.as_view(), name='staff_applications'),
    path('staff/application/<int:pk>/', views.ServiceApplicationDetailView.as_view(), name='staff_application_detail'),
    path('staff/application/<int:pk>/assess/', views.ServiceApplicationAssessmentView.as_view(), name='staff_application_assess'),
    path('staff/application/<int:application_id>/disbursement/', views.ServiceDisbursementCreateView.as_view(), name='staff_disbursement_create'),
    
    # Ministry Programs Admin Interface
    path('admin/', admin_views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/programs/', admin_views.ProgramListView.as_view(), name='program_list'),
    path('admin/programs/create/', admin_views.ProgramCreateView.as_view(), name='program_create'),
    path('admin/programs/<int:pk>/', admin_views.program_detail_view, name='program_detail'),
    path('admin/programs/<int:pk>/edit/', admin_views.ProgramUpdateView.as_view(), name='program_update'),
    path('admin/programs/<int:pk>/delete/', admin_views.program_delete_view, name='program_delete'),
    path('admin/programs/bulk-action/', admin_views.bulk_actions_view, name='program_bulk_action'),
    path('admin/programs/export/', admin_views.export_programs_view, name='program_export'),
    path('admin/programs/import/', admin_views.import_programs_view, name='program_import'),
    path('admin/programs/history/', admin_views.program_history_view, name='program_history'),
]
