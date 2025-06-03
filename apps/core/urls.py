from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('about/', views.AboutPageView.as_view(), name='about'),
    path('chapters-overview/', views.ChaptersPageView.as_view(), name='chapters_overview'),
    path('contact/', views.ContactPageView.as_view(), name='contact'),
    path('ministries-ppas/', views.MinistriesPPAsView.as_view(), name='ministries_ppas'),
    path('programs/', views.ProgramsView.as_view(), name='programs'),
    path('partner/', views.PartnerPageView.as_view(), name='partner'),
    path('donate/', views.DonatePageView.as_view(), name='donate'),
    
    # Mobile views
    path('mobile/', views.MobileServiceView.as_view(), name='mobile_services'),
    path('mobile/offline/', views.OfflineFormView.as_view(), name='mobile_offline'),
    
    # API endpoints
    path('api/mobile/sync/', views.mobile_sync_api, name='mobile_sync_api'),
    
    # PWA files
    path('service-worker.js', views.service_worker, name='service_worker'),
    path('manifest.json', views.manifest, name='manifest'),
    path('offline/', views.offline_page, name='offline'),
]