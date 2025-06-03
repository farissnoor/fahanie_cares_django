from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.http import HttpResponseRedirect
from .models import ServiceProgram, ServiceApplication, ServiceDisbursement, ServiceImpact
from .forms import ServiceApplicationForm, ServiceAssessmentForm, ServiceDisbursementForm
from utils.notion.services import (
    create_service_application_in_notion,
    update_service_application_in_notion,
    get_service_availability,
    generate_application_id
)
from utils.notifications import send_notification

class ServiceProgramListView(ListView):
    """
    Public view of all active service programs.
    """
    model = ServiceProgram
    template_name = 'services/program_list.html'
    context_object_name = 'programs'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = ServiceProgram.objects.filter(
            status='active',
            published_at__isnull=False
        )
        
        # Filter by type if provided
        program_type = self.request.GET.get('type')
        if program_type:
            queryset = queryset.filter(program_type=program_type)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(target_beneficiaries__icontains=search)
            )
        
        # Only show programs accepting applications
        if self.request.GET.get('accepting_only'):
            active_programs = []
            for program in queryset:
                if program.is_accepting_applications():
                    active_programs.append(program.id)
            queryset = queryset.filter(id__in=active_programs)
        
        return queryset.order_by('-start_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['program_types'] = ServiceProgram.PROGRAM_TYPES
        return context


class ServiceProgramDetailView(DetailView):
    """
    Public detail view of a service program.
    """
    model = ServiceProgram
    template_name = 'services/program_detail.html'
    context_object_name = 'program'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        program = self.get_object()
        
        # Check availability
        context['availability'] = get_service_availability(program)
        
        # Check if user has existing application
        if self.request.user.is_authenticated:
            context['existing_application'] = ServiceApplication.objects.filter(
                program=program,
                applicant=self.request.user
            ).first()
        
        # Get program statistics
        context['stats'] = {
            'total_applications': program.applications.count(),
            'approved_applications': program.applications.filter(status='approved').count(),
            'budget_utilization': (program.budget_utilized / program.total_budget * 100) if program.total_budget > 0 else 0,
            'capacity_utilization': (program.beneficiary_count / program.max_beneficiaries * 100) if program.max_beneficiaries > 0 else 0,
        }
        
        return context


class ServiceApplicationCreateView(LoginRequiredMixin, CreateView):
    """
    Create a service application.
    """
    model = ServiceApplication
    form_class = ServiceApplicationForm
    template_name = 'services/application_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.program = get_object_or_404(ServiceProgram, slug=kwargs['slug'])
        
        # Check if program is accepting applications
        if not self.program.is_accepting_applications():
            messages.error(request, "This program is not currently accepting applications.")
            return redirect('service_program_detail', slug=self.program.slug)
        
        # Check if user already has an application
        existing = ServiceApplication.objects.filter(
            program=self.program,
            applicant=request.user
        ).first()
        
        if existing:
            messages.warning(request, "You already have an application for this program.")
            return redirect('service_application_detail', pk=existing.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        application = form.save(commit=False)
        application.program = self.program
        application.applicant = self.request.user
        application.save()
        
        # Create in Notion
        try:
            from utils.notion.client import NotionService
            notion_service = NotionService()
            create_service_application_in_notion(
                application,
                notion_service,
                settings.NOTION_SERVICE_APPLICATION_DB_ID
            )
        except Exception as e:
            messages.warning(self.request, f"Application created but Notion sync failed: {str(e)}")
        
        # Send notification
        send_notification(
            self.request.user,
            'Application Submitted',
            f'Your application for {self.program.name} has been submitted successfully.'
        )
        
        messages.success(self.request, "Your application has been submitted successfully!")
        return redirect('service_application_detail', pk=application.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['program'] = self.program
        return context


class ServiceApplicationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    View application details.
    """
    model = ServiceApplication
    template_name = 'services/application_detail.html'
    context_object_name = 'application'
    
    def test_func(self):
        application = self.get_object()
        return (self.request.user == application.applicant or 
                self.request.user.is_staff_or_above())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application = self.get_object()
        
        # Get disbursements
        context['disbursements'] = application.disbursements.all().order_by('-scheduled_date')
        
        # Check if user can assess
        context['can_assess'] = self.request.user.is_staff_or_above()
        
        return context


class ServiceApplicationListView(LoginRequiredMixin, ListView):
    """
    View user's applications.
    """
    model = ServiceApplication
    template_name = 'services/application_list.html'
    context_object_name = 'applications'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = ServiceApplication.objects.filter(
            applicant=self.request.user
        )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = ServiceApplication.APPLICATION_STATUS
        return context


class StaffApplicationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Staff view of all applications.
    """
    model = ServiceApplication
    template_name = 'services/staff/application_list.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff_or_above()
    
    def get_queryset(self):
        queryset = ServiceApplication.objects.all()
        
        # Filter by program
        program_id = self.request.GET.get('program')
        if program_id:
            queryset = queryset.filter(program_id=program_id)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by priority
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority_level=priority)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(application_number__icontains=search) |
                Q(applicant__first_name__icontains=search) |
                Q(applicant__last_name__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['programs'] = ServiceProgram.objects.filter(status='active')
        context['status_choices'] = ServiceApplication.APPLICATION_STATUS
        context['priority_levels'] = ServiceApplication.PRIORITY_LEVELS
        
        # Get statistics
        queryset = self.get_queryset()
        context['stats'] = {
            'total': queryset.count(),
            'pending': queryset.filter(status='submitted').count(),
            'urgent': queryset.filter(priority_level='urgent').count(),
            'approved': queryset.filter(status='approved').count(),
        }
        
        return context


class ServiceApplicationAssessmentView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Assess a service application.
    """
    model = ServiceApplication
    form_class = ServiceAssessmentForm
    template_name = 'services/staff/application_assessment.html'
    
    def test_func(self):
        return self.request.user.is_staff_or_above()
    
    def form_valid(self, form):
        application = form.save(commit=False)
        application.reviewed_at = timezone.now()
        application.reviewed_by = self.request.user
        
        # Handle approval/rejection
        action = self.request.POST.get('action')
        if action == 'approve':
            application.approve(
                self.request.user,
                amount=form.cleaned_data.get('assistance_amount'),
                description=form.cleaned_data.get('assistance_description')
            )
            
            # Send notification
            send_notification(
                application.applicant,
                'Application Approved',
                f'Your application for {application.program.name} has been approved.'
            )
            
            messages.success(self.request, "Application approved successfully!")
            
        elif action == 'reject':
            application.reject(
                self.request.user,
                reason=form.cleaned_data.get('rejection_reason')
            )
            
            # Send notification
            send_notification(
                application.applicant,
                'Application Update',
                f'Your application for {application.program.name} has been reviewed. Please check the portal for details.'
            )
            
            messages.success(self.request, "Application rejected.")
        
        else:
            application.save()
            messages.success(self.request, "Assessment saved.")
        
        # Update in Notion
        try:
            from utils.notion.client import NotionService
            notion_service = NotionService()
            update_service_application_in_notion(application, notion_service)
        except Exception as e:
            messages.warning(self.request, f"Assessment saved but Notion sync failed: {str(e)}")
        
        return redirect('staff_application_detail', pk=application.pk)


class ServiceDisbursementCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create a disbursement for an approved application.
    """
    model = ServiceDisbursement
    form_class = ServiceDisbursementForm
    template_name = 'services/staff/disbursement_form.html'
    
    def test_func(self):
        return self.request.user.is_staff_or_above()
    
    def dispatch(self, request, *args, **kwargs):
        self.application = get_object_or_404(ServiceApplication, pk=kwargs['application_id'])
        
        # Check if application is approved
        if self.application.status != 'approved':
            messages.error(request, "Cannot create disbursement for non-approved application.")
            return redirect('staff_application_detail', pk=self.application.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        disbursement = form.save(commit=False)
        disbursement.application = self.application
        disbursement.save()
        
        messages.success(self.request, "Disbursement scheduled successfully!")
        return redirect('staff_application_detail', pk=self.application.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['application'] = self.application
        return context
    
    def get_initial(self):
        initial = super().get_initial()
        initial['amount'] = self.application.assistance_amount
        initial['recipient_name'] = self.application.applicant.get_full_name()
        return initial


class ServiceProgramDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Service program dashboard for staff.
    """
    template_name = 'services/staff/dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff_or_above()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get programs
        context['programs'] = ServiceProgram.objects.all().order_by('-created_at')
        
        # Get overall statistics
        context['overall_stats'] = {
            'total_programs': ServiceProgram.objects.count(),
            'active_programs': ServiceProgram.objects.filter(status='active').count(),
            'total_applications': ServiceApplication.objects.count(),
            'pending_applications': ServiceApplication.objects.filter(status='submitted').count(),
            'total_beneficiaries': ServiceProgram.objects.aggregate(
                total=Sum('beneficiary_count')
            )['total'] or 0,
            'total_budget': ServiceProgram.objects.aggregate(
                total=Sum('total_budget')
            )['total'] or 0,
            'budget_utilized': ServiceProgram.objects.aggregate(
                total=Sum('budget_utilized')
            )['total'] or 0,
        }
        
        # Get recent applications
        context['recent_applications'] = ServiceApplication.objects.filter(
            status='submitted'
        ).order_by('-created_at')[:10]
        
        # Get upcoming disbursements
        context['upcoming_disbursements'] = ServiceDisbursement.objects.filter(
            status='pending',
            scheduled_date__gte=timezone.now().date()
        ).order_by('scheduled_date')[:10]
        
        return context