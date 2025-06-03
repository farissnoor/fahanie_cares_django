from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search_view, name='search'),
    path('advanced/', views.advanced_search_view, name='advanced_search'),
    path('saved/', views.saved_searches_view, name='saved_searches'),
    path('save/', views.save_search_view, name='save_search'),
    path('saved/<uuid:search_id>/use/', views.use_saved_search_view, name='use_saved_search'),
    path('saved/<uuid:search_id>/delete/', views.delete_saved_search_view, name='delete_saved_search'),
    path('history/', views.search_history_view, name='search_history'),
    path('history/clear/', views.clear_search_history_view, name='clear_search_history'),
    path('api/suggestions/', views.search_suggestions_api, name='suggestions_api'),
    path('export/', views.export_search_results_view, name='export_results'),
]