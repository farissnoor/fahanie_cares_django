from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # Document management
    path('', views.document_list, name='document_list'),
    path('upload/', views.document_upload, name='document_upload'),
    path('<uuid:pk>/', views.document_detail, name='document_detail'),
    path('<uuid:pk>/download/', views.document_download, name='document_download'),
    path('<uuid:pk>/new-version/', views.document_new_version, name='document_new_version'),
    path('<uuid:pk>/approve-reject/', views.document_approve_reject, name='document_approve_reject'),
    
    # Templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/<int:pk>/download/', views.template_download, name='template_download'),
    
    # API endpoints
    path('api/search/', views.document_search_api, name='document_search_api'),
]