from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Main notification views
    path('', views.notification_list, name='notification_list'),
    path('<uuid:pk>/', views.notification_detail, name='notification_detail'),
    path('<uuid:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('<uuid:pk>/delete/', views.delete_notification, name='delete_notification'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    
    # Preferences
    path('preferences/', views.notification_preferences, name='notification_preferences'),
    path('history/', views.notification_history, name='notification_history'),
    
    # API endpoints
    path('api/unread-count/', views.get_unread_count, name='get_unread_count'),
    path('api/recent/', views.get_recent_notifications, name='get_recent_notifications'),
]