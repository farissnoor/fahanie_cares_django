from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, UpdateView, CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Avg, F, Sum
import datetime
import logging

from .models import Constituent, ConstituentInteraction, ConstituentGroup
from apps.users.models import User
from utils.notion.client import NotionService

logger = logging.getLogger(__name__)

class StaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin that checks if the user is a staff member or above.
    """
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff_or_above()

# Staff Constituent Views
class StaffConstituentDashboardView(StaffRequiredMixin, ListView):
    """
    Dashboard for staff to view and manage constituents.
    """
    model = Constituent
    template_name = 'constituents/staff/dashboard.html'
    context_object_name = 'constituents'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = Constituent.objects.all().select_related('user')
        
        # Filter by search query if provided
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) | 
                Q(user__last_name__icontains=search_query) | 
                Q(user__email__icontains=search_query) |
                Q(user__phone_number__icontains=search_query) |
                Q(voter_id__icontains=search_query)
            )
        
        # Filter by engagement level if provided
        engagement_level = self.request.GET.get('engagement_level')
        if engagement_level:
            if engagement_level == 'high':
                queryset = queryset.filter(engagement_level__gte=7)
            elif engagement_level == 'medium':
                queryset = queryset.filter(engagement_level__range=(4, 6))
            elif engagement_level == 'low':
                queryset = queryset.filter(engagement_level__range=(1, 3))
            elif engagement_level == 'inactive':
                queryset = queryset.filter(engagement_level=0)
        
        # Filter by voter status if provided
        is_voter = self.request.GET.get('is_voter')
        if is_voter:
            is_voter_bool = is_voter == 'true'
            queryset = queryset.filter(is_voter=is_voter_bool)
        
        # Filter by volunteer status if provided
        is_volunteer = self.request.GET.get('is_volunteer')
        if is_volunteer:
            is_volunteer_bool = is_volunteer == 'true'
            queryset = queryset.filter(is_volunteer=is_volunteer_bool)
        
        # Filter by gender if provided
        gender = self.request.GET.get('gender')
        if gender:
            queryset = queryset.filter(gender=gender)
        
        # Filter by group if provided
        group_id = self.request.GET.get('group')
        if group_id:
            queryset = queryset.filter(groups__id=group_id)
            
        # Sort results
        sort_by = self.request.GET.get('sort_by', '-created_at')
        if sort_by == 'name':
            queryset = queryset.order_by('user__first_name', 'user__last_name')
        elif sort_by == 'engagement_high':
            queryset = queryset.order_by('-engagement_level')
        elif sort_by == 'engagement_low':
            queryset = queryset.order_by('engagement_level')
        elif sort_by == 'recent_engagement':
            queryset = queryset.order_by('-last_engagement')
        else:
            queryset = queryset.order_by(sort_by)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get counts for sidebar filters
        context['engagement_counts'] = {
            'high': Constituent.objects.filter(engagement_level__gte=7).count(),
            'medium': Constituent.objects.filter(engagement_level__range=(4, 6)).count(),
            'low': Constituent.objects.filter(engagement_level__range=(1, 3)).count(),
            'inactive': Constituent.objects.filter(engagement_level=0).count(),
        }
        
        context['voter_counts'] = {
            'voters': Constituent.objects.filter(is_voter=True).count(),
            'non_voters': Constituent.objects.filter(is_voter=False).count(),
        }
        
        context['volunteer_counts'] = {
            'volunteers': Constituent.objects.filter(is_volunteer=True).count(),
            'non_volunteers': Constituent.objects.filter(is_volunteer=False).count(),
        }
        
        # Get all constituent groups for filtering
        context['groups'] = ConstituentGroup.objects.all().annotate(member_count=Count('members'))
        
        # Get selected filters for active state in UI
        context['selected_engagement_level'] = self.request.GET.get('engagement_level', '')
        context['selected_is_voter'] = self.request.GET.get('is_voter', '')
        context['selected_is_volunteer'] = self.request.GET.get('is_volunteer', '')
        context['selected_gender'] = self.request.GET.get('gender', '')
        context['selected_group'] = self.request.GET.get('group', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['sort_by'] = self.request.GET.get('sort_by', '-created_at')
        
        # Base params for pagination links
        filter_params = self.request.GET.copy()
        if 'page' in filter_params:
            del filter_params['page']
        context['filter_params'] = filter_params
        
        # Quick stats
        context['total_constituents'] = Constituent.objects.count()
        context['new_this_month'] = Constituent.objects.filter(
            created_at__gte=timezone.now().replace(day=1, hour=0, minute=0)
        ).count()
        context['avg_engagement'] = Constituent.objects.aggregate(avg=Avg('engagement_level'))['avg'] or 0
        
        return context
    
class StaffConstituentDetailView(StaffRequiredMixin, DetailView):
    """
    Detailed view of a constituent for staff members.
    """
    model = Constituent
    template_name = 'constituents/staff/detail.html'
    context_object_name = 'constituent'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        constituent = self.get_object()
        
        # Get all interactions for this constituent
        context['interactions'] = constituent.interactions.all().select_related('staff_member').order_by('-date')
        
        # Get all groups this constituent belongs to
        context['groups'] = constituent.groups.all()
        
        # Get referrals if available (assuming a relationship exists)
        try:
            from apps.referrals.models import Referral
            context['referrals'] = Referral.objects.filter(constituent=constituent.user).order_by('-created_at')
        except ImportError:
            # Referrals app might not be installed or no relationship exists
            context['referrals'] = []
        
        return context

class StaffConstituentCreateView(StaffRequiredMixin, CreateView):
    """
    Create a new constituent profile.
    """
    model = Constituent
    template_name = 'constituents/staff/form.html'
    fields = ['birth_date', 'gender', 'education_level', 'occupation', 'occupation_type', 
              'household_size', 'is_voter', 'voter_id', 'voting_center', 'alternate_contact', 
              'bio', 'profile_image', 'interests', 'language_preference', 'is_volunteer', 
              'volunteer_interests', 'notes']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Constituent'
        context['submit_text'] = 'Create Constituent'
        return context
    
    def form_valid(self, form):
        # Get or create the user first
        email = self.request.POST.get('email')
        phone = self.request.POST.get('phone_number')
        first_name = self.request.POST.get('first_name')
        last_name = self.request.POST.get('last_name')
        
        # Check if user with this email already exists
        try:
            user = User.objects.get(email=email)
            # If user exists but already has a constituent profile, prevent duplicate
            if hasattr(user, 'constituent_profile'):
                messages.error(self.request, f"User with email {email} already has a constituent profile.")
                return self.form_invalid(form)
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone,
                user_type='constituent'
            )
            
        # Now save the constituent profile
        constituent = form.save(commit=False)
        constituent.user = user
        constituent.created_at = timezone.now()
        constituent.updated_at = timezone.now()
        
        # Set membership date if they're becoming a member
        if self.request.POST.get('is_member') == 'on':
            constituent.membership_date = timezone.now().date()
            user.user_type = 'member'
            user.save()
        
        constituent.save()
        
        # Save to Notion if integration is available
        try:
            notion_service = NotionService()
            notion_id = notion_service.create_constituent(constituent)
            if notion_id:
                constituent.notion_id = notion_id
                constituent.save(update_fields=['notion_id'])
        except Exception as e:
            logger.error(f"Error saving constituent to Notion: {e}")
            
        messages.success(self.request, f"Constituent profile for {user.get_full_name()} created successfully.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('staff_constituent_detail', kwargs={'pk': self.object.pk})

class StaffConstituentUpdateView(StaffRequiredMixin, UpdateView):
    """
    Update an existing constituent profile.
    """
    model = Constituent
    template_name = 'constituents/staff/form.html'
    fields = ['birth_date', 'gender', 'education_level', 'occupation', 'occupation_type', 
              'household_size', 'is_voter', 'voter_id', 'voting_center', 'alternate_contact', 
              'bio', 'profile_image', 'interests', 'language_preference', 'engagement_level',
              'is_volunteer', 'volunteer_interests', 'notes']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Constituent'
        context['submit_text'] = 'Save Changes'
        # Pass user information to the template for display in the form
        context['user_data'] = self.object.user
        return context
    
    def form_valid(self, form):
        # Update user information if provided
        user = self.object.user
        if user:
            user.first_name = self.request.POST.get('first_name', user.first_name)
            user.last_name = self.request.POST.get('last_name', user.last_name)
            user.email = self.request.POST.get('email', user.email)
            user.phone_number = self.request.POST.get('phone_number', user.phone_number)
            
            # Update user type if membership status changes
            if self.request.POST.get('is_member') == 'on' and user.user_type == 'constituent':
                user.user_type = 'member'
                if not self.object.membership_date:
                    form.instance.membership_date = timezone.now().date()
            
            user.save()
        
        # Update the constituent record
        constituent = form.save(commit=False)
        constituent.updated_at = timezone.now()
        constituent.save()
        
        # Update in Notion if integration is available
        if constituent.notion_id:
            try:
                notion_service = NotionService()
                notion_service.update_constituent(constituent)
            except Exception as e:
                logger.error(f"Error updating constituent in Notion: {e}")
        
        messages.success(self.request, f"Constituent profile for {user.get_full_name()} updated successfully.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('staff_constituent_detail', kwargs={'pk': self.object.pk})

class StaffConstituentInteractionCreateView(StaffRequiredMixin, CreateView):
    """
    Record a new interaction with a constituent.
    """
    model = ConstituentInteraction
    template_name = 'constituents/staff/interaction_form.html'
    fields = ['interaction_type', 'date', 'description', 'location', 'outcome', 'follow_up_date', 'follow_up_notes']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        constituent_id = self.kwargs.get('constituent_id')
        constituent = get_object_or_404(Constituent, id=constituent_id)
        context['constituent'] = constituent
        context['title'] = f'Record Interaction with {constituent.user.get_full_name()}'
        context['submit_text'] = 'Save Interaction'
        return context
    
    def form_valid(self, form):
        constituent_id = self.kwargs.get('constituent_id')
        constituent = get_object_or_404(Constituent, id=constituent_id)
        
        interaction = form.save(commit=False)
        interaction.constituent = constituent
        interaction.staff_member = self.request.user
        interaction.created_at = timezone.now()
        interaction.updated_at = timezone.now()
        interaction.save()
        
        # Update the constituent's last engagement date
        constituent.last_engagement = interaction.date.date()
        constituent.save(update_fields=['last_engagement'])
        
        # Update in Notion if integration is available
        try:
            notion_service = NotionService()
            notion_id = notion_service.create_constituent_interaction(interaction)
            if notion_id:
                interaction.notion_id = notion_id
                interaction.save(update_fields=['notion_id'])
        except Exception as e:
            logger.error(f"Error saving interaction to Notion: {e}")
        
        messages.success(self.request, f"Interaction with {constituent.user.get_full_name()} recorded successfully.")
        return redirect('staff_constituent_detail', pk=constituent.id)

class StaffConstituentGroupListView(StaffRequiredMixin, ListView):
    """
    List of constituent groups for staff management.
    """
    model = ConstituentGroup
    template_name = 'constituents/staff/group_list.html'
    context_object_name = 'groups'
    
    def get_queryset(self):
        return ConstituentGroup.objects.all().annotate(
            member_count=Count('members')
        ).order_by('-is_active', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_groups_count'] = ConstituentGroup.objects.filter(is_active=True).count()
        context['total_groups_count'] = ConstituentGroup.objects.count()
        return context

class StaffConstituentGroupDetailView(StaffRequiredMixin, DetailView):
    """
    Detailed view of a constituent group.
    """
    model = ConstituentGroup
    template_name = 'constituents/staff/group_detail.html'
    context_object_name = 'group'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        
        # Get all members of this group with their profiles
        context['members'] = group.members.all().select_related('user')
        
        return context

class StaffConstituentGroupCreateView(StaffRequiredMixin, CreateView):
    """
    Create a new constituent group.
    """
    model = ConstituentGroup
    template_name = 'constituents/staff/group_form.html'
    fields = ['name', 'description', 'is_active']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Group'
        context['submit_text'] = 'Create Group'
        return context
    
    def form_valid(self, form):
        group = form.save(commit=False)
        group.created_by = self.request.user
        group.created_at = timezone.now()
        group.updated_at = timezone.now()
        group.save()
        
        # Add initial members if provided
        member_ids = self.request.POST.getlist('members')
        if member_ids:
            constituents = Constituent.objects.filter(id__in=member_ids)
            group.members.add(*constituents)
        
        # Save to Notion if integration is available
        try:
            notion_service = NotionService()
            notion_id = notion_service.create_constituent_group(group)
            if notion_id:
                group.notion_id = notion_id
                group.save(update_fields=['notion_id'])
        except Exception as e:
            logger.error(f"Error saving group to Notion: {e}")
        
        messages.success(self.request, f"Constituent group '{group.name}' created successfully.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('staff_constituent_group_detail', kwargs={'slug': self.object.slug})

class StaffConstituentGroupUpdateView(StaffRequiredMixin, UpdateView):
    """
    Update an existing constituent group.
    """
    model = ConstituentGroup
    template_name = 'constituents/staff/group_form.html'
    fields = ['name', 'description', 'is_active']
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Group'
        context['submit_text'] = 'Save Changes'
        
        # Get current members for display in the form
        context['current_members'] = self.object.members.all()
        return context
    
    def form_valid(self, form):
        group = form.save(commit=False)
        group.updated_at = timezone.now()
        group.save()
        
        # Update members if needed
        member_ids = self.request.POST.getlist('members')
        if member_ids:
            group.members.clear()
            constituents = Constituent.objects.filter(id__in=member_ids)
            group.members.add(*constituents)
        
        # Update in Notion if integration is available
        if group.notion_id:
            try:
                notion_service = NotionService()
                notion_service.update_constituent_group(group)
            except Exception as e:
                logger.error(f"Error updating group in Notion: {e}")
        
        messages.success(self.request, f"Constituent group '{group.name}' updated successfully.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('staff_constituent_group_detail', kwargs={'slug': self.object.slug})

class StaffConstituentAnalyticsView(StaffRequiredMixin, TemplateView):
    """
    Analytics dashboard for constituent data.
    """
    template_name = 'constituents/staff/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Overall counts
        context['total_constituents'] = Constituent.objects.count()
        context['total_voters'] = Constituent.objects.filter(is_voter=True).count()
        context['total_volunteers'] = Constituent.objects.filter(is_volunteer=True).count()
        
        # Demographics
        context['gender_distribution'] = Constituent.objects.exclude(gender='').values('gender').annotate(
            count=Count('id')
        ).order_by('gender')
        
        context['education_distribution'] = Constituent.objects.exclude(education_level='').values('education_level').annotate(
            count=Count('id')
        ).order_by('education_level')
        
        context['occupation_distribution'] = Constituent.objects.exclude(occupation_type='').values('occupation_type').annotate(
            count=Count('id')
        ).order_by('occupation_type')
        
        # Engagement metrics
        context['avg_engagement'] = Constituent.objects.aggregate(avg=Avg('engagement_level'))['avg'] or 0
        context['engagement_distribution'] = {
            'high': Constituent.objects.filter(engagement_level__gte=7).count(),
            'medium': Constituent.objects.filter(engagement_level__range=(4, 6)).count(),
            'low': Constituent.objects.filter(engagement_level__range=(1, 3)).count(),
            'inactive': Constituent.objects.filter(engagement_level=0).count(),
        }
        
        # Growth over time (by month for the past year)
        end_date = timezone.now()
        start_date = end_date - datetime.timedelta(days=365)
        
        growth_data = []
        current_date = start_date
        
        while current_date <= end_date:
            month_start = current_date.replace(day=1)
            if current_date.month == 12:
                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                month_end = current_date.replace(month=current_date.month + 1, day=1)
                
            count = Constituent.objects.filter(created_at__gte=month_start, created_at__lt=month_end).count()
            growth_data.append({
                'period': month_start.strftime('%b %Y'),
                'count': count
            })
            
            current_date = month_end
        
        context['growth_data'] = growth_data
        
        return context