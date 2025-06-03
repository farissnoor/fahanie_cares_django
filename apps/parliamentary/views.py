from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from datetime import date, timedelta

from .models import (
    LegislativeSession, LegislativeMeasure, LegislativeAction,
    Committee, CommitteeMembership, CommitteeHearing,
    PlenarySession, SpeechPrivilege, OversightActivity, VotingRecord
)


class ParliamentaryDashboardView(LoginRequiredMixin, ListView):
    """Main dashboard for parliamentary work."""
    model = LegislativeMeasure
    template_name = 'parliamentary/dashboard.html'
    context_object_name = 'recent_measures'
    
    def get_queryset(self):
        return self.model.objects.filter(
            Q(principal_author=self.request.user) | Q(co_authors=self.request.user)
        ).order_by('-last_action_date')[:5]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Current session
        context['current_session'] = LegislativeSession.objects.filter(is_current=True).first()
        
        # My legislation statistics
        context['my_measures_count'] = LegislativeMeasure.objects.filter(
            Q(principal_author=user) | Q(co_authors=user)
        ).count()
        
        context['my_active_measures'] = LegislativeMeasure.objects.filter(
            Q(principal_author=user) | Q(co_authors=user),
            status__in=['filed', 'committee', 'plenary']
        ).count()
        
        # Committee memberships
        context['my_committees'] = CommitteeMembership.objects.filter(
            member=user,
            is_active=True
        ).select_related('committee')
        
        # Upcoming hearings
        context['upcoming_hearings'] = CommitteeHearing.objects.filter(
            committee__memberships__member=user,
            committee__memberships__is_active=True,
            scheduled_date__gte=timezone.now()
        ).order_by('scheduled_date')[:5]
        
        # Recent speeches
        context['recent_speeches'] = SpeechPrivilege.objects.filter(
            speaker=user
        ).order_by('-plenary_session__session_date')[:3]
        
        # Oversight activities
        context['my_oversight'] = OversightActivity.objects.filter(
            Q(lead_member=user) | Q(committee__memberships__member=user)
        ).filter(status='ongoing').distinct()[:5]
        
        return context


class LegislativeMeasureListView(LoginRequiredMixin, ListView):
    """List all legislative measures with filtering."""
    model = LegislativeMeasure
    template_name = 'parliamentary/measure_list.html'
    context_object_name = 'measures'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('session', 'principal_author')
        
        # Filter by session
        session_id = self.request.GET.get('session')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by type
        measure_type = self.request.GET.get('type')
        if measure_type:
            queryset = queryset.filter(measure_type=measure_type)
        
        # Search
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(number__icontains=query) |
                Q(title__icontains=query) |
                Q(short_title__icontains=query) |
                Q(abstract__icontains=query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sessions'] = LegislativeSession.objects.all()
        context['status_choices'] = LegislativeMeasure.STATUS_CHOICES
        context['type_choices'] = LegislativeMeasure.TYPE_CHOICES
        context['query'] = self.request.GET.get('q', '')
        context['selected_session'] = self.request.GET.get('session', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_type'] = self.request.GET.get('type', '')
        return context


class LegislativeMeasureDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a legislative measure."""
    model = LegislativeMeasure
    template_name = 'parliamentary/measure_detail.html'
    context_object_name = 'measure'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        measure = self.object
        
        # Get all actions
        context['actions'] = measure.actions.all().order_by('-action_date')
        
        # Get related measures
        context['related_measures'] = measure.related_measures.all()
        
        # Get voting records
        context['voting_records'] = measure.votes.all().select_related('member', 'voting_session')
        
        # Get speeches related to this measure
        context['related_speeches'] = SpeechPrivilege.objects.filter(
            related_measure=measure
        ).select_related('speaker', 'plenary_session')
        
        # Check if user can edit
        context['can_edit'] = (
            self.request.user == measure.principal_author or
            self.request.user in measure.co_authors.all() or
            self.request.user.is_staff
        )
        
        return context


class LegislativeMeasureCreateView(LoginRequiredMixin, CreateView):
    """Create a new legislative measure."""
    model = LegislativeMeasure
    template_name = 'parliamentary/measure_form.html'
    fields = [
        'session', 'measure_type', 'number', 'title', 'short_title',
        'abstract', 'full_text_url', 'co_authors', 'priority',
        'primary_committee', 'secondary_committees', 'beneficiaries',
        'estimated_budget', 'implementation_timeline'
    ]
    
    def form_valid(self, form):
        form.instance.principal_author = self.request.user
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Legislative measure created successfully.')
        return super().form_valid(form)


class CommitteeListView(LoginRequiredMixin, ListView):
    """List all committees."""
    model = Committee
    template_name = 'parliamentary/committee_list.html'
    context_object_name = 'committees'
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True).annotate(
            member_count=Count('memberships', filter=Q(memberships__is_active=True))
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's committee memberships
        context['my_committees'] = CommitteeMembership.objects.filter(
            member=self.request.user,
            is_active=True
        ).select_related('committee').values_list('committee_id', flat=True)
        
        return context


class CommitteeDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a committee."""
    model = Committee
    template_name = 'parliamentary/committee_detail.html'
    context_object_name = 'committee'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        committee = self.object
        
        # Get current members
        context['current_members'] = committee.memberships.filter(
            is_active=True
        ).select_related('member').order_by('role', 'member__last_name')
        
        # Get recent hearings
        context['recent_hearings'] = committee.hearings.all().order_by('-scheduled_date')[:10]
        
        # Get measures in committee
        context['measures_in_committee'] = LegislativeMeasure.objects.filter(
            primary_committee=committee.name,
            status='committee'
        ).order_by('-filed_date')[:10]
        
        # Check if user is a member
        context['is_member'] = committee.memberships.filter(
            member=self.request.user,
            is_active=True
        ).exists()
        
        # Get subcommittees
        context['subcommittees'] = committee.subcommittees.filter(is_active=True)
        
        return context


class CommitteeHearingDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a committee hearing."""
    model = CommitteeHearing
    template_name = 'parliamentary/hearing_detail.html'
    context_object_name = 'hearing'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if user is a committee member
        context['is_committee_member'] = self.object.committee.memberships.filter(
            member=self.request.user,
            is_active=True
        ).exists()
        
        return context


class OversightActivityListView(LoginRequiredMixin, ListView):
    """List oversight activities."""
    model = OversightActivity
    template_name = 'parliamentary/oversight_list.html'
    context_object_name = 'activities'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('committee', 'lead_member')
        
        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by type
        activity_type = self.request.GET.get('type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        # Search
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(target_agency__icontains=query) |
                Q(target_program__icontains=query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = OversightActivity.STATUS_CHOICES
        context['type_choices'] = OversightActivity.ACTIVITY_TYPES
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_type'] = self.request.GET.get('type', '')
        context['query'] = self.request.GET.get('q', '')
        return context


class OversightActivityDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of an oversight activity."""
    model = OversightActivity
    template_name = 'parliamentary/oversight_detail.html'
    context_object_name = 'activity'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if user can edit
        context['can_edit'] = (
            self.request.user == self.object.lead_member or
            self.request.user == self.object.created_by or
            self.request.user.is_staff
        )
        
        return context


class PlenarySessionListView(LoginRequiredMixin, ListView):
    """List plenary sessions."""
    model = PlenarySession
    template_name = 'parliamentary/plenary_list.html'
    context_object_name = 'sessions'
    paginate_by = 20
    
    def get_queryset(self):
        return super().get_queryset().select_related('session').order_by('-session_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get upcoming sessions
        context['upcoming_sessions'] = PlenarySession.objects.filter(
            session_date__gte=date.today()
        ).order_by('session_date')[:5]
        
        return context


class SpeechPrivilegeListView(LoginRequiredMixin, ListView):
    """List speeches and privileges."""
    model = SpeechPrivilege
    template_name = 'parliamentary/speech_list.html'
    context_object_name = 'speeches'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('speaker', 'plenary_session')
        
        # Filter by speaker (for "My Speeches" view)
        if self.request.GET.get('my_speeches'):
            queryset = queryset.filter(speaker=self.request.user)
        
        # Filter by type
        speech_type = self.request.GET.get('type')
        if speech_type:
            queryset = queryset.filter(speech_type=speech_type)
        
        # Search
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(summary__icontains=query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type_choices'] = SpeechPrivilege.SPEECH_TYPES
        context['selected_type'] = self.request.GET.get('type', '')
        context['query'] = self.request.GET.get('q', '')
        context['showing_my_speeches'] = self.request.GET.get('my_speeches', False)
        return context


@login_required
def record_action(request, measure_id):
    """Record an action on a legislative measure."""
    measure = get_object_or_404(LegislativeMeasure, id=measure_id)
    
    # Check permissions
    if not (request.user == measure.principal_author or request.user.is_staff):
        messages.error(request, 'You do not have permission to record actions on this measure.')
        return redirect('parliamentary:measure_detail', pk=measure_id)
    
    if request.method == 'POST':
        action = LegislativeAction(
            measure=measure,
            action_type=request.POST.get('action_type'),
            description=request.POST.get('description'),
            vote_yes=request.POST.get('vote_yes') or None,
            vote_no=request.POST.get('vote_no') or None,
            vote_abstain=request.POST.get('vote_abstain') or None,
            recorded_by=request.user
        )
        action.save()
        
        # Update measure's last action date
        measure.last_action_date = action.action_date.date()
        
        # Update status based on action type
        if action.action_type == 'filed':
            measure.status = 'filed'
            measure.filed_date = action.action_date.date()
        elif action.action_type == 'referred':
            measure.status = 'committee'
        elif action.action_type == 'approved_committee':
            measure.status = 'plenary'
        elif action.action_type == 'approved':
            measure.status = 'approved_house'
        elif action.action_type == 'transmitted':
            measure.status = 'transmitted'
        elif action.action_type == 'enrolled':
            measure.status = 'enrolled'
        elif action.action_type == 'signed':
            measure.status = 'enacted'
        elif action.action_type == 'vetoed':
            measure.status = 'vetoed'
        
        measure.save()
        
        messages.success(request, 'Action recorded successfully.')
        return redirect('parliamentary:measure_detail', pk=measure_id)
    
    return render(request, 'parliamentary/record_action.html', {
        'measure': measure,
        'action_types': LegislativeAction.ACTION_TYPES
    })


@login_required
@require_http_methods(["POST"])
def record_vote(request, measure_id):
    """Record a vote on a legislative measure."""
    measure = get_object_or_404(LegislativeMeasure, id=measure_id)
    
    # Get current plenary session
    plenary_session = PlenarySession.objects.filter(
        session_date=date.today()
    ).first()
    
    if not plenary_session:
        return JsonResponse({'error': 'No plenary session today'}, status=400)
    
    # Check if vote already exists
    existing_vote = VotingRecord.objects.filter(
        measure=measure,
        member=request.user,
        voting_session=plenary_session
    ).first()
    
    if existing_vote:
        # Update existing vote
        existing_vote.vote = request.POST.get('vote')
        existing_vote.reasoning = request.POST.get('reasoning', '')
        existing_vote.save()
        message = 'Vote updated successfully.'
    else:
        # Create new vote
        vote = VotingRecord(
            measure=measure,
            member=request.user,
            voting_session=plenary_session,
            vote=request.POST.get('vote'),
            reasoning=request.POST.get('reasoning', '')
        )
        vote.save()
        message = 'Vote recorded successfully.'
    
    return JsonResponse({'message': message})