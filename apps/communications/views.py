from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from .models import (
    CommunicationTemplate, CommunicationCampaign, CommunicationMessage,
    AnnouncementPost, EventNotification, CommunicationSettings
)
from .forms import (
    CampaignForm, TemplateForm, AnnouncementForm, CommunicationSettingsForm,
    MessageComposeForm
)
from apps.users.models import User

class AnnouncementListView(ListView):
    """
    Public list of announcements.
    """
    model = AnnouncementPost
    template_name = 'communications/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = AnnouncementPost.objects.filter(
            status='published',
            published_date__lte=timezone.now()
        )
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(summary__icontains=search) |
                Q(content__icontains=search)
            )
        
        # Check targeting if user is authenticated
        if self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(target_all=True) |
                Q(target_chapters__memberships__user=self.request.user) |
                Q(target_user_types__contains=self.request.user.user_type)
            ).distinct()
        else:
            queryset = queryset.filter(target_all=True)
        
        # Order by pinned first, then featured, then date
        return queryset.order_by('-is_pinned', '-is_featured', '-published_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = AnnouncementPost.POST_CATEGORIES
        return context


class AnnouncementDetailView(DetailView):
    """
    Public detail view of an announcement.
    """
    model = AnnouncementPost
    template_name = 'communications/announcement_detail.html'
    context_object_name = 'announcement'
    
    def get_queryset(self):
        return AnnouncementPost.objects.filter(
            status='published',
            published_date__lte=timezone.now()
        )


class CampaignListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    List communication campaigns (staff only).
    """
    model = CommunicationCampaign
    template_name = 'communications/campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff_or_above()
    
    def get_queryset(self):
        queryset = CommunicationCampaign.objects.select_related('template', 'created_by')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['campaign_stats'] = {
            'draft': CommunicationCampaign.objects.filter(status='draft').count(),
            'scheduled': CommunicationCampaign.objects.filter(status='scheduled').count(),
            'sent': CommunicationCampaign.objects.filter(status='sent').count(),
        }
        return context


class CampaignCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create a new campaign (staff only).
    """
    model = CommunicationCampaign
    form_class = CampaignForm
    template_name = 'communications/campaign_form.html'
    success_url = reverse_lazy('campaign_list')
    
    def test_func(self):
        return self.request.user.is_staff_or_above()
    
    def form_valid(self, form):
        campaign = form.save(commit=False)
        campaign.created_by = self.request.user
        
        # Calculate recipients
        recipients = campaign.get_recipients()
        campaign.total_recipients = len(recipients)
        
        campaign.save()
        form.save_m2m()  # Save many-to-many fields
        
        messages.success(
            self.request,
            f"Campaign created with {campaign.total_recipients} recipients."
        )
        return super().form_valid(form)


class CampaignDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    View campaign details (staff only).
    """
    model = CommunicationCampaign
    template_name = 'communications/campaign_detail.html'
    context_object_name = 'campaign'
    
    def test_func(self):
        return self.request.user.is_staff_or_above()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        campaign = self.get_object()
        
        # Get message statistics
        messages_qs = campaign.messages.all()
        context['message_stats'] = {
            'total': messages_qs.count(),
            'sent': messages_qs.filter(status='sent').count(),
            'delivered': messages_qs.filter(status='delivered').count(),
            'read': messages_qs.filter(status='read').count(),
            'failed': messages_qs.filter(status='failed').count(),
        }
        
        # Get recent messages
        context['recent_messages'] = messages_qs.order_by('-created_at')[:10]
        
        return context


class CampaignSendView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Send a campaign (staff only).
    """
    model = CommunicationCampaign
    fields = []
    template_name = 'communications/campaign_send.html'
    
    def test_func(self):
        campaign = self.get_object()
        return (self.request.user.is_staff_or_above() and 
                campaign.status in ['draft', 'scheduled'])
    
    def form_valid(self, form):
        campaign = self.get_object()
        
        # Send immediately or schedule
        if self.request.POST.get('send_now'):
            campaign.send()
            messages.success(self.request, "Campaign is being sent.")
        else:
            scheduled_time = self.request.POST.get('scheduled_time')
            if scheduled_time:
                campaign.scheduled_time = scheduled_time
                campaign.status = 'scheduled'
                campaign.save()
                messages.success(
                    self.request,
                    f"Campaign scheduled for {campaign.scheduled_time}"
                )
        
        return redirect('campaign_detail', pk=campaign.pk)


class MessageInboxView(LoginRequiredMixin, ListView):
    """
    User's message inbox.
    """
    model = CommunicationMessage
    template_name = 'communications/message_inbox.html'
    context_object_name = 'messages'
    paginate_by = 20
    
    def get_queryset(self):
        return CommunicationMessage.objects.filter(
            recipient=self.request.user
        ).select_related('campaign').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Unread count
        context['unread_count'] = CommunicationMessage.objects.filter(
            recipient=self.request.user,
            status__in=['sent', 'delivered']
        ).count()
        
        return context


class MessageDetailView(LoginRequiredMixin, DetailView):
    """
    View message details.
    """
    model = CommunicationMessage
    template_name = 'communications/message_detail.html'
    context_object_name = 'message'
    
    def get_object(self):
        message = get_object_or_404(
            CommunicationMessage,
            pk=self.kwargs['pk'],
            recipient=self.request.user
        )
        
        # Mark as read
        message.mark_as_read()
        
        return message


class NotificationListView(LoginRequiredMixin, ListView):
    """
    User's notifications.
    """
    model = EventNotification
    template_name = 'communications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return EventNotification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Unread count
        context['unread_count'] = EventNotification.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).count()
        
        return context


class NotificationMarkReadView(LoginRequiredMixin, UpdateView):
    """
    Mark notification as read (AJAX).
    """
    model = EventNotification
    fields = []
    
    def post(self, request, *args, **kwargs):
        notification = self.get_object()
        
        # Verify ownership
        if notification.recipient != request.user:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        notification.mark_as_read()
        
        return JsonResponse({
            'status': 'success',
            'is_read': notification.is_read
        })


class CommunicationSettingsView(LoginRequiredMixin, UpdateView):
    """
    User communication preferences.
    """
    model = CommunicationSettings
    form_class = CommunicationSettingsForm
    template_name = 'communications/settings.html'
    success_url = reverse_lazy('communication_settings')
    
    def get_object(self, queryset=None):
        # Get or create settings for current user
        settings, created = CommunicationSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings
    
    def form_valid(self, form):
        messages.success(self.request, "Communication preferences updated.")
        return super().form_valid(form)


class ComposeMessageView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Compose a direct message (staff only).
    """
    model = CommunicationMessage
    form_class = MessageComposeForm
    template_name = 'communications/compose_message.html'
    
    def test_func(self):
        return self.request.user.is_staff_or_above()
    
    def form_valid(self, form):
        message = form.save(commit=False)
        
        # Send the message
        from .tasks import send_single_message
        send_single_message.delay(message.id)
        
        messages.success(
            self.request,
            f"Message sent to {message.recipient.get_full_name()}"
        )
        
        return redirect('message_compose')


class AnnouncementCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create announcement (staff only).
    """
    model = AnnouncementPost
    form_class = AnnouncementForm
    template_name = 'communications/announcement_form.html'
    success_url = reverse_lazy('announcement_list')
    
    def test_func(self):
        return self.request.user.is_staff_or_above()
    
    def form_valid(self, form):
        announcement = form.save(commit=False)
        announcement.author = self.request.user
        announcement.save()
        form.save_m2m()
        
        messages.success(self.request, "Announcement created successfully.")
        return super().form_valid(form)


class CommunicationDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Communication dashboard for staff.
    """
    template_name = 'communications/dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff_or_above()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Campaign statistics
        campaigns = CommunicationCampaign.objects.all()
        context['campaign_stats'] = {
            'total': campaigns.count(),
            'draft': campaigns.filter(status='draft').count(),
            'scheduled': campaigns.filter(status='scheduled').count(),
            'sent': campaigns.filter(status='sent').count(),
            'total_recipients': campaigns.aggregate(
                total=Sum('total_recipients')
            )['total'] or 0,
        }
        
        # Message statistics
        messages_qs = CommunicationMessage.objects.all()
        context['message_stats'] = {
            'total': messages_qs.count(),
            'sent': messages_qs.filter(status='sent').count(),
            'delivered': messages_qs.filter(status='delivered').count(),
            'read': messages_qs.filter(status='read').count(),
            'failed': messages_qs.filter(status='failed').count(),
        }
        
        # Recent campaigns
        context['recent_campaigns'] = campaigns.order_by('-created_at')[:5]
        
        # Recent announcements
        context['recent_announcements'] = AnnouncementPost.objects.order_by(
            '-created_at'
        )[:5]
        
        # Communication preferences
        context['preference_stats'] = {
            'email_enabled': CommunicationSettings.objects.filter(
                email_enabled=True
            ).count(),
            'sms_enabled': CommunicationSettings.objects.filter(
                sms_enabled=True
            ).count(),
            'marketing_allowed': CommunicationSettings.objects.filter(
                allow_marketing=True
            ).count(),
        }
        
        return context