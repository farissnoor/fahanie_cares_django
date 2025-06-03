from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views.generic.edit import FormMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponseRedirect
import logging

from .models import Agency, ServiceCategory, Service, Referral, ReferralUpdate, ReferralDocument
from apps.users.models import User
from utils.notion.client import NotionService
from utils.notifications import NotificationService

logger = logging.getLogger(__name__)

class ServiceCategoryListView(ListView):
    """
    Display all service categories.
    """
    model = ServiceCategory
    template_name = 'referrals/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        # Only return parent categories
        return ServiceCategory.objects.filter(parent__isnull=True).order_by('order', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subcategories'] = ServiceCategory.objects.filter(parent__isnull=False).order_by('parent__name', 'order', 'name')
        return context

class ServiceListView(ListView):
    """
    Display services, optionally filtered by category.
    """
    model = Service
    template_name = 'referrals/service_list.html'
    context_object_name = 'services'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Service.objects.filter(is_active=True)
        
        # Filter by category if provided
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(ServiceCategory, slug=category_slug)
            if category.parent is None:
                # If it's a parent category, include all services from subcategories
                subcategories = ServiceCategory.objects.filter(parent=category)
                queryset = queryset.filter(Q(category=category) | Q(category__in=subcategories))
            else:
                queryset = queryset.filter(category=category)
        
        # Filter by search query if provided
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(agency__name__icontains=search_query)
            )
        
        return queryset.order_by('category__name', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add categories for sidebar filter
        context['categories'] = ServiceCategory.objects.filter(parent__isnull=True).order_by('order', 'name')
        
        # Add currently selected category
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['selected_category'] = get_object_or_404(ServiceCategory, slug=category_slug)
        
        # Add search query
        context['search_query'] = self.request.GET.get('q', '')
        
        return context

class ServiceDetailView(DetailView):
    """
    Display detailed information about a service.
    """
    model = Service
    template_name = 'referrals/service_detail.html'
    context_object_name = 'service'
    slug_url_kwarg = 'service_slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add related services from same category
        context['related_services'] = Service.objects.filter(
            category=self.object.category,
            is_active=True
        ).exclude(pk=self.object.pk)[:4]
        
        return context

class ReferralCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new service referral.
    """
    model = Referral
    template_name = 'referrals/referral_create.html'
    fields = ['description', 'supporting_documents']
    
    def dispatch(self, request, *args, **kwargs):
        # Get the service
        self.service = get_object_or_404(Service, slug=self.kwargs.get('service_slug'), is_active=True)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service'] = self.service
        return context
    
    def form_valid(self, form):
        form.instance.constituent = self.request.user
        form.instance.service = self.service
        form.instance.status = 'submitted'
        form.instance.submitted_at = timezone.now()
        
        response = super().form_valid(form)
        
        # Create initial referral update
        ReferralUpdate.objects.create(
            referral=self.object,
            status='submitted',
            notes="Referral submitted by constituent",
            created_by=self.request.user
        )
        
        # Send to Notion if configured
        try:
            notion_service = NotionService()
            notion_service.create_referral(self.object)
        except Exception as e:
            # Log the error but don't prevent referral creation
            logger.error(f"Error creating Notion record: {str(e)}")
        
        messages.success(self.request, f"Your referral has been submitted successfully. Your reference number is {self.object.reference_number}")
        return response
    
    def get_success_url(self):
        return reverse('referral_detail', kwargs={'reference_number': self.object.reference_number})

class ReferralDetailView(LoginRequiredMixin, DetailView):
    """
    Display detailed information about a referral.
    """
    model = Referral
    template_name = 'referrals/referral_detail.html'
    context_object_name = 'referral'
    
    def get_object(self):
        return get_object_or_404(
            Referral,
            reference_number=self.kwargs.get('reference_number'),
            constituent=self.request.user
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['updates'] = self.object.updates.all().order_by('-created_at')
        context['documents'] = self.object.documents.all().order_by('-created_at')
        return context

class ReferralListView(LoginRequiredMixin, ListView):
    """
    Display all referrals for the current user.
    """
    model = Referral
    template_name = 'referrals/referral_list.html'
    context_object_name = 'referrals'
    paginate_by = 10
    
    def get_queryset(self):
        return Referral.objects.filter(constituent=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Count referrals by status
        context['total_referrals'] = self.get_queryset().count()
        context['draft_count'] = self.get_queryset().filter(status='draft').count()
        context['submitted_count'] = self.get_queryset().filter(status='submitted').count()
        context['processing_count'] = self.get_queryset().filter(status__in=['reviewing', 'processing', 'referred']).count()
        context['completed_count'] = self.get_queryset().filter(status__in=['approved', 'completed']).count()
        context['denied_count'] = self.get_queryset().filter(status='denied').count()
        
        return context

class ReferralUpdateCreateView(LoginRequiredMixin, CreateView):
    """
    Add an update comment to a referral.
    """
    model = ReferralUpdate
    fields = ['notes']
    template_name = 'referrals/referral_update_create.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.referral = get_object_or_404(
            Referral,
            reference_number=self.kwargs.get('reference_number'),
            constituent=self.request.user
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['referral'] = self.referral
        return context
    
    def form_valid(self, form):
        form.instance.referral = self.referral
        form.instance.status = self.referral.status  # Keep the current status
        form.instance.created_by = self.request.user
        
        response = super().form_valid(form)
        
        messages.success(self.request, "Your update has been added to the referral.")
        return response
    
    def get_success_url(self):
        return reverse('referral_detail', kwargs={'reference_number': self.referral.reference_number})

class ReferralDocumentCreateView(LoginRequiredMixin, CreateView):
    """
    Add a document to a referral.
    """
    model = ReferralDocument
    fields = ['name', 'file']
    template_name = 'referrals/referral_document_create.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.referral = get_object_or_404(
            Referral,
            reference_number=self.kwargs.get('reference_number'),
            constituent=self.request.user
        )
        
        # Only allow document uploads for non-completed referrals
        if self.referral.status in ['completed', 'denied', 'cancelled']:
            messages.error(request, "You cannot add documents to a closed referral.")
            return redirect('referral_detail', reference_number=self.referral.reference_number)
            
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['referral'] = self.referral
        return context
    
    def form_valid(self, form):
        form.instance.referral = self.referral
        form.instance.uploaded_by = self.request.user
        
        response = super().form_valid(form)
        
        # Create an update about the document
        update = ReferralUpdate.objects.create(
            referral=self.referral,
            status=self.referral.status,
            notes=f"Document '{form.instance.name}' uploaded by constituent",
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
            
        # Send notification to staff members
        # Note: For constituent document uploads, we only notify staff
        # but don't send notification back to the constituent who uploaded it
        try:
            staff_users = User.objects.filter(user_type__in=['staff', 'mp'])
            if staff_users.exists() and hasattr(self.referral, 'assigned_to') and self.referral.assigned_to:
                # We're calling a slightly different method since this is for staff notification
                NotificationService.send_document_upload_notification(form.instance)
        except Exception as e:
            logger.error(f"Failed to send staff notification: {str(e)}")
        
        messages.success(self.request, "Your document has been uploaded successfully.")
        return response
    
    def get_success_url(self):
        return reverse('referral_detail', kwargs={'reference_number': self.referral.reference_number})
