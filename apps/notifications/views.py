from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import Notification, NotificationPreference, NotificationType
from .forms import NotificationPreferenceForm, NotificationTypePreferenceForm, NotificationFilterForm


@login_required
def notification_list(request):
    """List user's notifications with filtering."""
    notifications = request.user.notifications.all()
    form = NotificationFilterForm(request.GET)
    
    # Apply filters
    if request.GET.get('type'):
        notifications = notifications.filter(type=request.GET.get('type'))
    
    if request.GET.get('status'):
        if request.GET.get('status') == 'unread':
            notifications = notifications.filter(is_read=False)
        elif request.GET.get('status') == 'read':
            notifications = notifications.filter(is_read=True)
    
    if request.GET.get('priority'):
        notifications = notifications.filter(priority=request.GET.get('priority'))
    
    if request.GET.get('date_from'):
        notifications = notifications.filter(created_at__gte=request.GET.get('date_from'))
    
    if request.GET.get('date_to'):
        notifications = notifications.filter(created_at__lte=request.GET.get('date_to'))
    
    # Apply ordering
    notifications = notifications.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Count unread notifications
    unread_count = request.user.notifications.filter(is_read=False).count()
    
    context = {
        'notifications': page_obj,
        'form': form,
        'unread_count': unread_count,
    }
    return render(request, 'notifications/notification_list.html', context)


@login_required
def notification_detail(request, pk):
    """View notification detail and mark as read."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    
    # Mark as read
    notification.mark_as_read()
    
    context = {
        'notification': notification,
    }
    return render(request, 'notifications/notification_detail.html', context)


@login_required
@require_http_methods(['POST'])
def mark_notification_read(request, pk):
    """Mark a notification as read via AJAX."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    
    return JsonResponse({
        'status': 'success',
        'is_read': notification.is_read,
        'read_at': notification.read_at.isoformat() if notification.read_at else None,
    })


@login_required
@require_http_methods(['POST'])
def mark_all_read(request):
    """Mark all notifications as read."""
    count = request.user.notifications.filter(is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'count': count,
        })
    
    messages.success(request, f'Marked {count} notification(s) as read.')
    return redirect('notifications:notification_list')


@login_required
def notification_preferences(request):
    """User notification preferences."""
    # Get or create user preferences
    preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=preferences)
        type_form = NotificationTypePreferenceForm(request.POST, user=request.user)
        
        if form.is_valid() and type_form.is_valid():
            form.save()
            type_form.save(request.user)
            messages.success(request, 'Notification preferences updated successfully.')
            return redirect('notifications:notification_preferences')
    else:
        form = NotificationPreferenceForm(instance=preferences)
        type_form = NotificationTypePreferenceForm(user=request.user)
    
    context = {
        'form': form,
        'type_form': type_form,
        'preferences': preferences,
    }
    return render(request, 'notifications/notification_preferences.html', context)


@login_required
def notification_history(request):
    """View notification history with statistics."""
    # Get date range filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    notifications = request.user.notifications.all()
    
    if date_from:
        notifications = notifications.filter(created_at__gte=date_from)
    if date_to:
        notifications = notifications.filter(created_at__lte=date_to)
    
    # Calculate statistics
    total_count = notifications.count()
    read_count = notifications.filter(is_read=True).count()
    unread_count = notifications.filter(is_read=False).count()
    
    # Count by type
    type_counts = {}
    for choice in NotificationType.choices:
        count = notifications.filter(type=choice[0]).count()
        if count > 0:
            type_counts[choice[1]] = count
    
    # Recent notifications
    recent_notifications = notifications.order_by('-created_at')[:10]
    
    context = {
        'total_count': total_count,
        'read_count': read_count,
        'unread_count': unread_count,
        'type_counts': type_counts,
        'recent_notifications': recent_notifications,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'notifications/notification_history.html', context)


# API endpoints for real-time notifications
@login_required
def get_unread_count(request):
    """Get current unread notification count."""
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def get_recent_notifications(request):
    """Get recent unread notifications for dropdown."""
    limit = int(request.GET.get('limit', 5))
    notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')[:limit]
    
    data = []
    for notification in notifications:
        data.append({
            'id': str(notification.id),
            'type': notification.type,
            'title': notification.title,
            'message': notification.message[:100] + '...' if len(notification.message) > 100 else notification.message,
            'priority': notification.priority,
            'created_at': notification.created_at.isoformat(),
            'url': notification.data.get('url', '#'),
        })
    
    return JsonResponse({
        'notifications': data,
        'total_unread': request.user.notifications.filter(is_read=False).count(),
    })


@login_required
@require_http_methods(['DELETE'])
def delete_notification(request, pk):
    """Delete a notification."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    messages.success(request, 'Notification deleted.')
    return redirect('notifications:notification_list')