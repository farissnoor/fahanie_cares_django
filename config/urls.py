"""
URL configuration for #FahanieCares project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Customize admin site
admin.site.site_header = "#FahanieCares Administration"
admin.site.site_title = "#FahanieCares Admin"
admin.site.index_title = "Welcome to #FahanieCares Admin Panel"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.users.urls')),
    path('services/', include('apps.services.urls')),  # Moved before referrals to avoid conflicts
    path('', include('apps.referrals.urls')),
    path('staff/referrals/', include('apps.referrals.staff_urls')),
    path('', include('apps.constituents.urls')),
    path('chapters/', include('apps.chapters.urls')),
    path('documents/', include('apps.documents.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('search/', include('apps.search.urls')),
    path('dashboards/', include('apps.dashboards.urls')),
    # Add other app URLs as they're created
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)