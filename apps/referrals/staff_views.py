from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, UpdateView, CreateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponseRedirect
from datetime import date, timedelta
import logging

from .models import Referral, ReferralUpdate, ReferralDocument, Agency, Service, ServiceCategory
from apps.users.models import User
from utils.notion.client import NotionService
from utils.notifications import NotificationService
from . import analytics

logger = logging.getLogger(__name__)

class StaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin that checks if the user is a staff member or above.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff_or_above()

class StaffDashboardView(StaffRequiredMixin, ListView):
    """
    Dashboard for staff to view all referrals.
    """
    model = Referral
    template_name = 'referrals/staff/dashboard.html'
    context_object_name = 'referrals'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = Referral.objects.all().select_related('constituent', 'service', 'service__agency', 'service__category')
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by search query if provided
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(reference_number__icontains=search_query) | 
                Q(constituent__first_name__icontains=search_query) |
                Q(constituent__last_name__icontains=search_query) |
                Q(service__name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filter by agency if provided
        agency_id = self.request.GET.get('agency')
        if agency_id:
            queryset = queryset.filter(service__agency_id=agency_id)
            
        # Filter by service category if provided
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(
                Q(service__category_id=category_id) | 
                Q(service__category__parent_id=category_id)
            )
        
        # Filter by priority if provided
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
            
        # Filter by date range if provided
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            try:
                from datetime import datetime
                date_from = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=date_from)
            except ValueError:
                pass
                
        if date_to:
            try:
                from datetime import datetime, timedelta
                date_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(created_at__lt=date_to)
            except ValueError:
                pass
        
        # Filter by assigned staff if provided
        assigned_to = self.request.GET.get('assigned_to')
        if assigned_to:
            if assigned_to == 'unassigned':
                queryset = queryset.filter(assigned_to__isnull=True)
            elif assigned_to == 'me':
                queryset = queryset.filter(assigned_to=self.request.user)
            else:
                queryset = queryset.filter(assigned_to_id=assigned_to)
        
        # Filter by follow-up date if provided
        follow_up = self.request.GET.get('follow_up')
        if follow_up:
            from datetime import date
            if follow_up == 'today':
                queryset = queryset.filter(follow_up_date=date.today())
            elif follow_up == 'overdue':
                queryset = queryset.filter(follow_up_date__lt=date.today())
            elif follow_up == 'upcoming':
                queryset = queryset.filter(follow_up_date__gt=date.today())
            elif follow_up == 'this_week':
                today = date.today()
                end_of_week = today + timedelta(days=(6 - today.weekday()))
                queryset = queryset.filter(follow_up_date__range=[today, end_of_week])
        
        # Sort by parameter
        sort_by = self.request.GET.get('sort_by', '-created_at')
        if sort_by == 'priority_high':
            # Sort by priority (high to low) and then by created date
            priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
            queryset = sorted(queryset, key=lambda x: (priority_order.get(x.priority, 4), -x.created_at.timestamp()))
        else:
            valid_sort_fields = [
                'reference_number', 'created_at', '-created_at', 
                'updated_at', '-updated_at', 'status', 'priority',
                'constituent__first_name', '-constituent__first_name',
                'service__name', '-service__name',
                'service__agency__name', '-service__agency__name',
                'follow_up_date', '-follow_up_date'
            ]
            if sort_by in valid_sort_fields:
                queryset = queryset.order_by(sort_by)
            else:
                queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add status counts for the sidebar
        context['status_counts'] = {
            'all': Referral.objects.count(),
            'draft': Referral.objects.filter(status='draft').count(),
            'submitted': Referral.objects.filter(status='submitted').count(),
            'reviewing': Referral.objects.filter(status='reviewing').count(),
            'processing': Referral.objects.filter(status='processing').count(),
            'referred': Referral.objects.filter(status='referred').count(),
            'approved': Referral.objects.filter(status='approved').count(),
            'completed': Referral.objects.filter(status='completed').count(),
            'denied': Referral.objects.filter(status='denied').count(),
            'cancelled': Referral.objects.filter(status='cancelled').count(),
        }
        
        # Add priority counts
        context['priority_counts'] = {
            'urgent': Referral.objects.filter(priority='urgent').count(),
            'high': Referral.objects.filter(priority='high').count(),
            'medium': Referral.objects.filter(priority='medium').count(),
            'low': Referral.objects.filter(priority='low').count(),
        }
        
        # Add filter parameters to context for form persistence
        context['selected_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_agency'] = self.request.GET.get('agency', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_priority'] = self.request.GET.get('priority', '')
        context['selected_assigned_to'] = self.request.GET.get('assigned_to', '')
        context['selected_follow_up'] = self.request.GET.get('follow_up', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['sort_by'] = self.request.GET.get('sort_by', '-created_at')
        
        # Get all filter parameters to add to pagination links
        self.filter_params = self.request.GET.copy()
        if 'page' in self.filter_params:
            del self.filter_params['page']
        context['filter_params'] = self.filter_params
        
        # Add agencies for filtering
        context['agencies'] = Agency.objects.filter(is_active=True).order_by('name')
        
        # Add service categories for filtering
        context['categories'] = ServiceCategory.objects.filter(parent__isnull=True).order_by('name')
        context['subcategories'] = ServiceCategory.objects.filter(parent__isnull=False).order_by('parent__name', 'name')
        
        # Add staff users for filtering
        context['staff_users'] = User.objects.filter(
            user_type__in=['staff', 'mp']
        ).order_by('first_name', 'last_name')
        
        # Add referral choices for templates
        context['status_choices'] = Referral.STATUS_CHOICES
        context['priority_choices'] = Referral.PRIORITY_CHOICES
        
        # Add follow-up options
        from datetime import date
        today = date.today()
        context['today'] = today
        
        # Count follow-up dates
        context['follow_up_counts'] = {
            'today': Referral.objects.filter(follow_up_date=today).count(),
            'overdue': Referral.objects.filter(follow_up_date__lt=today).count(),
            'this_week': Referral.objects.filter(
                follow_up_date__range=[today, today + timedelta(days=(6 - today.weekday()))]
            ).count(),
            'has_date': Referral.objects.filter(follow_up_date__isnull=False).count(),
        }
        
        # Calculate average response time (first staff response after submission)
        submitted_referrals = Referral.objects.filter(
            submitted_at__isnull=False
        ).exclude(
            status='draft'
        )
        
        response_times = []
        
        for referral in submitted_referrals:
            first_update = referral.updates.exclude(
                created_by=referral.constituent
            ).order_by('created_at').first()
            
            if first_update and referral.submitted_at:
                response_time = first_update.created_at - referral.submitted_at
                response_times.append(response_time.total_seconds() / 86400)  # Days
        
        if response_times:
            context['avg_response_time'] = sum(response_times) / len(response_times)
        else:
            context['avg_response_time'] = None
            
        # Get completion stats
        context['completion_stats'] = analytics.get_completion_time_stats()
        
        # Count completed referrals this month
        this_month_start = today.replace(day=1)
        context['completed_this_month'] = Referral.objects.filter(
            status='completed',
            completed_at__gte=this_month_start
        ).count()
        
        return context

class StaffReferralDetailView(StaffRequiredMixin, DetailView):
    """
    Staff view for detailed referral information and management.
    """
    model = Referral
    template_name = 'referrals/staff/referral_detail.html'
    context_object_name = 'referral'
    
    def get_object(self):
        return get_object_or_404(
            Referral,
            reference_number=self.kwargs.get('reference_number')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add related data
        context['updates'] = self.object.updates.all().order_by('-created_at').select_related('created_by')
        context['documents'] = self.object.documents.all().order_by('-created_at').select_related('uploaded_by')
        
        # Add staff users for assignment
        context['staff_users'] = User.objects.filter(
            user_type__in=['staff', 'mp']
        ).order_by('first_name', 'last_name')
        
        return context

class StaffReferralUpdateView(StaffRequiredMixin, UpdateView):
    """
    Update referral status and details by staff.
    """
    model = Referral
    template_name = 'referrals/staff/referral_update.html'
    fields = [
        'status', 'priority', 'assigned_to', 'staff_notes', 
        'agency_contact', 'agency_reference', 'agency_notes', 'follow_up_date'
    ]
    
    def get_object(self):
        return get_object_or_404(
            Referral,
            reference_number=self.kwargs.get('reference_number')
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['staff_users'] = User.objects.filter(
            user_type__in=['staff', 'mp']
        ).order_by('first_name', 'last_name')
        return context
    
    def form_valid(self, form):
        old_status = self.object.status
        result = super().form_valid(form)
        
        # Create status update if status changed
        if old_status != form.instance.status:
            update_notes = self.request.POST.get('update_notes', '')
            if not update_notes:
                update_notes = f"Status changed from {self.object.get_status_display()} to {form.instance.get_status_display()}"
            
            update = ReferralUpdate.objects.create(
                referral=self.object,
                status=form.instance.status,
                notes=update_notes,
                created_by=self.request.user
            )
            
            # Send notification
            NotificationService.send_referral_status_notification(self.object, update)
            
            # Update timestamps based on status
            if form.instance.status == 'referred' and not form.instance.referred_at:
                form.instance.referred_at = timezone.now()
                form.instance.save(update_fields=['referred_at'])
            elif form.instance.status == 'completed' and not form.instance.completed_at:
                form.instance.completed_at = timezone.now()
                form.instance.save(update_fields=['completed_at'])
        
        # Update in Notion if configured
        try:
            notion_service = NotionService()
            notion_service.update_referral(self.object)
            
            # Also record the update in Notion
            latest_update = self.object.updates.order_by('-created_at').first()
            if latest_update:
                notion_service.create_referral_update(latest_update)
        except Exception as e:
            # Log the error but don't prevent update
            logger.error(f"Error updating Notion record: {str(e)}")
        
        messages.success(self.request, f"Referral {self.object.reference_number} has been updated successfully.")
        return result
    
    def get_success_url(self):
        return reverse('staff_referral_detail', kwargs={'reference_number': self.object.reference_number})

class StaffReferralUpdateCreateView(StaffRequiredMixin, CreateView):
    """
    Add a status update to a referral.
    """
    model = ReferralUpdate
    template_name = 'referrals/staff/referral_update_create.html'
    fields = ['status', 'notes']
    
    def dispatch(self, request, *args, **kwargs):
        self.referral = get_object_or_404(
            Referral,
            reference_number=self.kwargs.get('reference_number')
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        return {
            'status': self.referral.status
        }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['referral'] = self.referral
        return context
    
    def form_valid(self, form):
        form.instance.referral = self.referral
        form.instance.created_by = self.request.user
        
        # Update referral status if it's changed
        if form.instance.status != self.referral.status:
            old_status = self.referral.status
            self.referral.status = form.instance.status
            
            # Update timestamps based on new status
            if form.instance.status == 'referred' and not self.referral.referred_at:
                self.referral.referred_at = timezone.now()
            elif form.instance.status == 'completed' and not self.referral.completed_at:
                self.referral.completed_at = timezone.now()
                
            self.referral.save()
            
            # Update in Notion if configured
            try:
                notion_service = NotionService()
                notion_service.update_referral(self.referral)
                
                # Also record the update in Notion
                notion_service.create_referral_update(form.instance)
            except Exception as e:
                # Log the error but don't prevent update
                logger.error(f"Error updating Notion record: {str(e)}")
        
        response = super().form_valid(form)
        
        # Send notification - status update or comment notification depending on status change
        if form.instance.status != self.referral.status:
            NotificationService.send_referral_status_notification(self.referral, form.instance)
        else:
            NotificationService.send_referral_comment_notification(self.referral, form.instance)
        
        messages.success(self.request, "Your update has been added to the referral.")
        return response
    
    def get_success_url(self):
        return reverse('staff_referral_detail', kwargs={'reference_number': self.referral.reference_number})

class StaffDocumentUploadView(StaffRequiredMixin, CreateView):
    """
    Add a document to a referral.
    """
    model = ReferralDocument
    template_name = 'referrals/staff/document_upload.html'
    fields = ['name', 'file']
    
    def dispatch(self, request, *args, **kwargs):
        self.referral = get_object_or_404(
            Referral,
            reference_number=self.kwargs.get('reference_number')
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['referral'] = self.referral
        return context
    
    def form_valid(self, form):
        form.instance.referral = self.referral
        form.instance.uploaded_by = self.request.user
        
        response = super().form_valid(form)
        
        # Create update about the document
        update = ReferralUpdate.objects.create(
            referral=self.referral,
            status=self.referral.status,
            notes=f"Document '{form.instance.name}' uploaded by {self.request.user.get_full_name()} (Staff)",
            created_by=self.request.user
        )
        
        # Record in Notion if configured
        try:
            notion_service = NotionService()
            # Record the document upload
            notion_service.create_referral_document(form.instance)
            # Record the update entry
            notion_service.create_referral_update(update)
        except Exception as e:
            # Log the error but don't prevent document creation
            logger.error(f"Error recording document in Notion: {str(e)}")
            
        # Send notification
        NotificationService.send_document_upload_notification(form.instance)
        
        messages.success(self.request, "Document has been uploaded successfully.")
        return response
    
    def get_success_url(self):
        return reverse('staff_referral_detail', kwargs={'reference_number': self.referral.reference_number})

class AssignToMeView(StaffRequiredMixin, UpdateView):
    """
    Quick action to assign a referral to the current staff member.
    """
    model = Referral
    http_method_names = ['post']
    fields = ['assigned_to']
    
    def get_object(self):
        return get_object_or_404(
            Referral,
            reference_number=self.kwargs.get('reference_number')
        )
    
    def form_valid(self, form):
        form.instance.assigned_to = self.request.user
        result = super().form_valid(form)
        
        # Create an update
        ReferralUpdate.objects.create(
            referral=self.object,
            status=self.object.status,
            notes=f"Assigned to {self.request.user.get_full_name()}",
            created_by=self.request.user
        )
        
        messages.success(self.request, f"Referral {self.object.reference_number} has been assigned to you.")
        return result
    
    def get_success_url(self):
        return reverse('staff_referral_detail', kwargs={'reference_number': self.object.reference_number})