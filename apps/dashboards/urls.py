from django.urls import path
from . import views

app_name = 'dashboards'

urlpatterns = [
    path('', views.ExecutiveDashboardView.as_view(), name='executive'),
    path('operational/', views.operational_dashboard_view, name='operational'),
    path('chapters/', views.chapter_dashboard_view, name='chapter'),
    path('reports/', views.custom_report_view, name='custom_report'),
    path('api/<str:widget_type>/', views.dashboard_api_view, name='widget_api'),
    path('config/save/', views.save_dashboard_config, name='save_config'),
]