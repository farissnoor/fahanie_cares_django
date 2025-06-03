from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db.models import Q, Count, Sum
from .models import Chapter, ChapterMembership, ChapterActivity, ActivityAttendance
from .forms import ChapterForm, MembershipForm, ActivityForm, MembershipApplicationForm
from apps.users.models import User
from utils.notion.client import NotionService

class ChapterListView(ListView):
    """
    Public view of all active chapters.
    """
    model = Chapter
    template_name = 'chapters/chapter_list.html'
    context_object_name = 'chapters'
    paginate_by = 12
    
    def get_queryset(self):
        # Only show Provincial and Municipal/City chapters
        queryset = Chapter.objects.filter(status='active', tier__in=['provincial', 'municipal'])
        
        # Filter by municipality if provided
        municipality = self.request.GET.get('municipality')
        if municipality:
            queryset = queryset.filter(municipality=municipality)
        
        # Filter by tier if provided
        tier = self.request.GET.get('tier')
        if tier and tier in ['provincial', 'municipal']:  # Only allow provincial and municipal filters
            queryset = queryset.filter(tier=tier)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(municipality__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('tier', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['municipalities'] = Chapter.objects.filter(
            status='active', tier__in=['provincial', 'municipal']
        ).values_list('municipality', flat=True).distinct().order_by('municipality')
        
        # Add user memberships for template condition
        if self.request.user.is_authenticated:
            user_memberships = ChapterMembership.objects.filter(
                user=self.request.user
            ).values_list('chapter_id', flat=True)
            context['user_memberships'] = list(user_memberships)
        else:
            context['user_memberships'] = []
            
        return context


class ChapterDetailView(DetailView):
    """
    Public detail view of a chapter.
    """
    model = Chapter
    template_name = 'chapters/chapter_detail.html'
    context_object_name = 'chapter'
    
    def get_object(self):
        return get_object_or_404(Chapter, slug=self.kwargs['slug'], status='active', tier__in=['provincial', 'municipal'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        chapter = self.get_object()
        
        # Get leadership
        context['leadership'] = ChapterMembership.objects.filter(
            chapter=chapter,
            status='active',
            role__in=['coordinator', 'assistant_coordinator']
        ).select_related('user')
        
        # Get upcoming activities
        context['upcoming_activities'] = ChapterActivity.objects.filter(
            chapter=chapter,
            status__in=['planned', 'ongoing'],
            date__gte=timezone.now().date()
        ).order_by('date', 'start_time')[:5]
        
        # Check if user is a member
        if self.request.user.is_authenticated:
            context['user_membership'] = ChapterMembership.objects.filter(
                chapter=chapter,
                user=self.request.user
            ).first()
        
        # Get recent activities
        context['recent_activities'] = ChapterActivity.objects.filter(
            chapter=chapter,
            status='completed'
        ).order_by('-date')[:3]
        
        # Get member count by status
        context['member_stats'] = ChapterMembership.objects.filter(
            chapter=chapter
        ).values('status').annotate(count=Count('id'))
        
        return context


class ChapterCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Create a new chapter (staff only).
    """
    model = Chapter
    form_class = ChapterForm
    template_name = 'chapters/chapter_form.html'
    success_url = reverse_lazy('chapter_list')
    
    def test_func(self):
        return self.request.user.is_staff_or_above()
    
    def form_valid(self, form):
        chapter = form.save(commit=False)
        
        # If user is MP or staff, auto-approve
        if self.request.user.user_type in ['mp', 'staff']:
            chapter.status = 'active'
            chapter.approved_by = self.request.user
            chapter.approved_at = timezone.now()
        
        chapter.save()
        
        # Create in Notion
        try:
            notion_service = NotionService()
            # Create chapter in Notion database
            # This would be implemented based on Notion API setup
        except Exception as e:
            messages.warning(self.request, f"Chapter created locally but Notion sync failed: {str(e)}")
        
        messages.success(self.request, "Chapter created successfully!")
        return super().form_valid(form)


class ChapterUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update chapter details (coordinators and staff only).
    """
    model = Chapter
    form_class = ChapterForm
    template_name = 'chapters/chapter_form.html'
    
    def test_func(self):
        chapter = self.get_object()
        return (self.request.user.is_staff_or_above() or 
                chapter.coordinator == self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, "Chapter updated successfully!")
        return super().form_valid(form)


class MembershipApplicationView(LoginRequiredMixin, CreateView):
    """
    Apply for chapter membership.
    """
    model = ChapterMembership
    form_class = MembershipApplicationForm
    template_name = 'chapters/membership_application.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.chapter = get_object_or_404(Chapter, slug=kwargs['slug'], status='active', tier__in=['provincial', 'municipal'])
        
        # Check if user already has membership
        existing = ChapterMembership.objects.filter(
            chapter=self.chapter,
            user=request.user
        ).first()
        
        if existing:
            messages.warning(request, "You already have a membership application for this chapter.")
            return redirect('chapter_detail', slug=self.chapter.slug)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        membership = form.save(commit=False)
        membership.chapter = self.chapter
        membership.user = self.request.user
        membership.save()
        
        messages.success(
            self.request, 
            "Your membership application has been submitted and is pending approval."
        )
        return redirect('chapter_detail', slug=self.chapter.slug)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chapter'] = self.chapter
        return context


class ChapterMembershipView(LoginRequiredMixin, ListView):
    """
    View chapter members (members only).
    """
    model = ChapterMembership
    template_name = 'chapters/chapter_members.html'
    context_object_name = 'memberships'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        self.chapter = get_object_or_404(Chapter, slug=kwargs['slug'], tier__in=['provincial', 'municipal'])
        
        # Check if user is a member
        if not ChapterMembership.objects.filter(
            chapter=self.chapter,
            user=request.user,
            status='active'
        ).exists() and not request.user.is_staff_or_above():
            messages.error(request, "You must be a member to view the member list.")
            return redirect('chapter_detail', slug=self.chapter.slug)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return ChapterMembership.objects.filter(
            chapter=self.chapter,
            status='active'
        ).select_related('user').order_by('-role', 'user__last_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chapter'] = self.chapter
        
        # Get membership statistics
        context['stats'] = {
            'total_members': self.get_queryset().count(),
            'volunteers': self.get_queryset().filter(is_volunteer=True).count(),
            'committees': self.get_queryset().exclude(committees='').count(),
        }
        
        return context


class ChapterActivityListView(ListView):
    """
    List chapter activities.
    """
    model = ChapterActivity
    template_name = 'chapters/activity_list.html'
    context_object_name = 'activities'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        self.chapter = get_object_or_404(Chapter, slug=kwargs['slug'], tier__in=['provincial', 'municipal'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = ChapterActivity.objects.filter(chapter=self.chapter)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by type
        activity_type = self.request.GET.get('type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        return queryset.order_by('-date', '-start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chapter'] = self.chapter
        context['activity_types'] = ChapterActivity.ACTIVITY_TYPES
        context['status_choices'] = ChapterActivity.STATUS_CHOICES
        return context


class ChapterActivityDetailView(DetailView):
    """
    Activity detail view.
    """
    model = ChapterActivity
    template_name = 'chapters/activity_detail.html'
    context_object_name = 'activity'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activity = self.get_object()
        
        # Get attendance records
        context['attendance'] = ActivityAttendance.objects.filter(
            activity=activity
        ).select_related('attendee')
        
        # Check if user is registered
        if self.request.user.is_authenticated:
            context['user_attendance'] = ActivityAttendance.objects.filter(
                activity=activity,
                attendee=self.request.user
            ).first()
        
        return context


class ActivityRegistrationView(LoginRequiredMixin, CreateView):
    """
    Register for an activity.
    """
    model = ActivityAttendance
    fields = ['tasks_completed', 'feedback']
    template_name = 'chapters/activity_registration.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.activity = get_object_or_404(ChapterActivity, pk=kwargs['pk'])
        
        # Check if already registered
        if ActivityAttendance.objects.filter(
            activity=self.activity,
            attendee=request.user
        ).exists():
            messages.warning(request, "You are already registered for this activity.")
            return redirect('activity_detail', pk=self.activity.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        attendance = form.save(commit=False)
        attendance.activity = self.activity
        attendance.attendee = self.request.user
        attendance.save()
        
        messages.success(self.request, "You have successfully registered for this activity!")
        return redirect('activity_detail', pk=self.activity.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity'] = self.activity
        return context


class ChapterDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Chapter coordinator dashboard.
    """
    template_name = 'chapters/coordinator_dashboard.html'
    
    def test_func(self):
        self.chapter = get_object_or_404(Chapter, slug=self.kwargs['slug'], tier__in=['provincial', 'municipal'])
        membership = ChapterMembership.objects.filter(
            chapter=self.chapter,
            user=self.request.user,
            status='active'
        ).first()
        
        return (membership and membership.role in ['coordinator', 'assistant_coordinator']) or \
               self.request.user.is_staff_or_above()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['chapter'] = self.chapter
        
        # Get pending memberships
        context['pending_memberships'] = ChapterMembership.objects.filter(
            chapter=self.chapter,
            status='pending'
        ).count()
        
        # Get upcoming activities
        context['upcoming_activities'] = ChapterActivity.objects.filter(
            chapter=self.chapter,
            status__in=['planned', 'ongoing'],
            date__gte=timezone.now().date()
        ).count()
        
        # Get recent activities needing reports
        context['activities_needing_reports'] = ChapterActivity.objects.filter(
            chapter=self.chapter,
            status='completed',
            report=''
        ).count()
        
        # Get member statistics
        context['member_stats'] = {
            'active': ChapterMembership.objects.filter(
                chapter=self.chapter,
                status='active'
            ).count(),
            'volunteers': ChapterMembership.objects.filter(
                chapter=self.chapter,
                status='active',
                is_volunteer=True
            ).count(),
            'total_volunteer_hours': ChapterMembership.objects.filter(
                chapter=self.chapter,
                status='active',
                is_volunteer=True
            ).aggregate(total=Sum('volunteer_hours'))['total'] or 0
        }
        
        # Recent activities
        context['recent_activities'] = ChapterActivity.objects.filter(
            chapter=self.chapter
        ).order_by('-date')[:5]
        
        return context