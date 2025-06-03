from django.urls import path
from . import views

urlpatterns = [
    # Service Categories
    path('services/categories/', views.ServiceCategoryListView.as_view(), name='category_list'),
    
    # Services
    path('services/', views.ServiceListView.as_view(), name='service_list'),
    path('services/category/<slug:category_slug>/', views.ServiceListView.as_view(), name='service_list_by_category'),
    path('services/<slug:service_slug>/', views.ServiceDetailView.as_view(), name='service_detail'),
    
    # Referrals
    path('referrals/', views.ReferralListView.as_view(), name='referral_list'),
    path('referrals/<str:reference_number>/', views.ReferralDetailView.as_view(), name='referral_detail'),
    path('referrals/<str:reference_number>/update/', views.ReferralUpdateCreateView.as_view(), name='referral_update_create'),
    path('referrals/<str:reference_number>/document/add/', views.ReferralDocumentCreateView.as_view(), name='referral_document_create'),
    path('services/<slug:service_slug>/refer/', views.ReferralCreateView.as_view(), name='referral_create'),
]