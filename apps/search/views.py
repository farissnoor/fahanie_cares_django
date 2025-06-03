import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from .services import SearchService
from .forms import SearchForm, AdvancedSearchForm, SavedSearchForm
from .models import SavedSearch, SearchHistory, SearchSuggestion
import csv
import logging

logger = logging.getLogger(__name__)


def search_view(request):
    """Global search view."""
    form = SearchForm(request.GET or None)
    results = {}
    query = ''
    module = 'all'
    
    if form.is_valid():
        query = form.cleaned_data.get('query', '')
        module = form.cleaned_data.get('module', 'all')
        
        if query:
            search_service = SearchService()
            
            if module == 'all':
                results = search_service.global_search(query, user=request.user)
            else:
                results = {
                    module: search_service.search_module(
                        module, query=query, user=request.user
                    )
                }
    
    # Get popular searches
    search_service = SearchService()
    popular_searches = search_service.get_popular_searches(module)
    
    context = {
        'form': form,
        'results': results,
        'query': query,
        'module': module,
        'popular_searches': popular_searches,
    }
    
    return render(request, 'search/search.html', context)


@login_required
def advanced_search_view(request):
    """Advanced search view with filters."""
    form = AdvancedSearchForm(request.GET or None)
    results = []
    filters = {}
    
    if request.GET and form.is_valid():
        module = form.cleaned_data['module']
        query = form.cleaned_data.get('query', '')
        
        # Build filters based on module
        if module == 'constituents':
            if form.cleaned_data.get('municipality'):
                filters['municipality'] = form.cleaned_data['municipality']
            if form.cleaned_data.get('barangay'):
                filters['barangay'] = form.cleaned_data['barangay']
            if form.cleaned_data.get('chapter_member'):
                filters['chapter_member'] = True
                
        elif module == 'referrals':
            if form.cleaned_data.get('status'):
                filters['status'] = form.cleaned_data['status']
            if form.cleaned_data.get('category'):
                filters['category'] = form.cleaned_data['category']
            if form.cleaned_data.get('priority'):
                filters['priority'] = form.cleaned_data['priority']
        
        # Date range filters
        if form.cleaned_data.get('date_from'):
            filters['date_from'] = form.cleaned_data['date_from'].isoformat()
        if form.cleaned_data.get('date_to'):
            filters['date_to'] = form.cleaned_data['date_to'].isoformat()
        
        # Sort options
        sort = None
        if form.cleaned_data.get('sort_by') != 'relevance':
            sort = [{
                'property': form.cleaned_data['sort_by'],
                'direction': form.cleaned_data.get('sort_order', 'desc')
            }]
        
        # Perform search
        search_service = SearchService()
        results = search_service.search_module(
            module, query=query, filters=filters, sort=sort, user=request.user
        )
        
        # Paginate results
        paginator = Paginator(results, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        results = page_obj
    
    context = {
        'form': form,
        'results': results,
        'filters': filters,
    }
    
    return render(request, 'search/advanced_search.html', context)


@login_required
def saved_searches_view(request):
    """View saved searches."""
    saved_searches = SavedSearch.objects.filter(
        Q(user=request.user) | Q(is_public=True)
    ).order_by('-last_used')
    
    context = {
        'saved_searches': saved_searches,
    }
    
    return render(request, 'search/saved_searches.html', context)


@login_required
@require_http_methods(["POST"])
def save_search_view(request):
    """Save a search."""
    form = SavedSearchForm(request.POST)
    
    if form.is_valid():
        saved_search = form.save(commit=False)
        saved_search.user = request.user
        saved_search.query = request.POST.get('query', '')
        saved_search.module = request.POST.get('module', 'all')
        
        # Parse and save filters
        filters = {}
        for key, value in request.POST.items():
            if key.startswith('filter_'):
                filter_name = key.replace('filter_', '')
                filters[filter_name] = value
        saved_search.filters = filters
        
        saved_search.save()
        messages.success(request, 'Search saved successfully!')
        
        return redirect('search:saved_searches')
    
    return JsonResponse({'error': 'Invalid form data'}, status=400)


@login_required
def use_saved_search_view(request, search_id):
    """Use a saved search."""
    saved_search = get_object_or_404(
        SavedSearch,
        Q(id=search_id) & (Q(user=request.user) | Q(is_public=True))
    )
    
    # Increment use count
    saved_search.increment_use_count()
    
    # Redirect to search with parameters
    params = {
        'query': saved_search.query,
        'module': saved_search.module,
    }
    params.update(saved_search.filters)
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    
    if len(saved_search.filters) > 0:
        return redirect(f'/search/advanced/?{query_string}')
    else:
        return redirect(f'/search/?{query_string}')


@login_required
def delete_saved_search_view(request, search_id):
    """Delete a saved search."""
    saved_search = get_object_or_404(SavedSearch, id=search_id, user=request.user)
    saved_search.delete()
    messages.success(request, 'Saved search deleted successfully!')
    return redirect('search:saved_searches')


@login_required
def search_history_view(request):
    """View search history."""
    history = SearchHistory.objects.filter(user=request.user)[:50]
    
    context = {
        'search_history': history,
    }
    
    return render(request, 'search/history.html', context)


@login_required
def clear_search_history_view(request):
    """Clear search history."""
    if request.method == 'POST':
        SearchHistory.objects.filter(user=request.user).delete()
        messages.success(request, 'Search history cleared successfully!')
    
    return redirect('search:search_history')


def search_suggestions_api(request):
    """API endpoint for search suggestions."""
    query = request.GET.get('q', '')
    module = request.GET.get('module', '')
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    search_service = SearchService()
    suggestions = search_service.get_search_suggestions(query, module)
    
    return JsonResponse({'suggestions': suggestions})


@login_required
def export_search_results_view(request):
    """Export search results to CSV."""
    # Get search parameters from request
    query = request.GET.get('query', '')
    module = request.GET.get('module', 'all')
    filters = {}
    
    # Parse filters from GET parameters
    for key, value in request.GET.items():
        if key.startswith('filter_'):
            filter_name = key.replace('filter_', '')
            filters[filter_name] = value
    
    # Perform search
    search_service = SearchService()
    
    if module == 'all':
        results = search_service.global_search(query, user=request.user, limit=None)
    else:
        results = {
            module: search_service.search_module(
                module, query=query, filters=filters, user=request.user, limit=None
            )
        }
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="search_results_{module}.csv"'
    
    writer = csv.writer(response)
    
    # Write headers
    if module == 'all':
        writer.writerow(['Module', 'Title', 'Details', 'Created', 'Modified'])
        
        # Write data for each module
        for module_name, module_results in results.items():
            for item in module_results:
                writer.writerow([
                    module_name,
                    item.get('display_title', ''),
                    json.dumps(item.get('properties', {})),
                    item.get('created_time', ''),
                    item.get('last_edited_time', ''),
                ])
    else:
        # Module-specific export
        module_results = results.get(module, [])
        
        if module_results:
            # Get all unique property keys
            all_properties = set()
            for item in module_results:
                all_properties.update(item.get('properties', {}).keys())
            
            # Write headers
            headers = ['Title'] + list(all_properties) + ['Created', 'Modified']
            writer.writerow(headers)
            
            # Write data
            for item in module_results:
                row = [item.get('display_title', '')]
                properties = item.get('properties', {})
                
                for prop in all_properties:
                    value = properties.get(prop, '')
                    if isinstance(value, list):
                        value = ', '.join(value)
                    row.append(value)
                
                row.extend([
                    item.get('created_time', ''),
                    item.get('last_edited_time', ''),
                ])
                
                writer.writerow(row)
    
    return response