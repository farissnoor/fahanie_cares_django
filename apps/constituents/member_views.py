from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.db.models import Q
from .member_models import FahanieCaresMember
from .member_forms import FahanieCaresMemberRegistrationForm, FahanieCaresMemberUpdateForm


class FahanieCaresMemberRegistrationView(CreateView):
    """
    View for new #FahanieCares member registration
    """
    form_class = FahanieCaresMemberRegistrationForm
    template_name = 'constituents/member_registration.html'
    success_url = reverse_lazy('registration_success')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, 
            'Your #FahanieCares membership application has been submitted successfully! '
            'You will receive an email once your application is approved.'
        )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '#FahanieCares Member Registration'
        return context


class RegistrationSuccessView(DetailView):
    """
    Success page after registration
    """
    template_name = 'constituents/registration_success.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {
            'title': 'Registration Successful'
        })


@method_decorator(login_required, name='dispatch')
class MemberProfileView(DetailView):
    """
    View for members to see their own profile
    """
    model = FahanieCaresMember
    template_name = 'constituents/member_profile.html'
    context_object_name = 'member'
    
    def get_object(self, queryset=None):
        try:
            return FahanieCaresMember.objects.get(user=self.request.user)
        except FahanieCaresMember.DoesNotExist:
            return None
    
    def get_context_data(self, **kwargs):
        # Override to handle None object
        context = {
            'member': self.get_object(),
            'title': 'My #FahanieCares Profile',
            'view': self
        }
        return context


@method_decorator(login_required, name='dispatch')
class MemberUpdateView(UpdateView):
    """
    View for members to update their profile
    """
    model = FahanieCaresMember
    form_class = FahanieCaresMemberUpdateForm
    template_name = 'constituents/member_update.html'
    success_url = reverse_lazy('member_profile')
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user has a member profile, redirect to registration if not
        try:
            FahanieCaresMember.objects.get(user=request.user)
        except FahanieCaresMember.DoesNotExist:
            messages.info(
                request, 
                'You need to complete your member registration first.'
            )
            return redirect('member_register')
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        return FahanieCaresMember.objects.get(user=self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Your profile has been updated successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update My Profile'
        return context


@method_decorator(login_required, name='dispatch')
class MemberListView(ListView):
    """
    Staff view to see all members
    """
    model = FahanieCaresMember
    template_name = 'constituents/staff/member_list.html'
    context_object_name = 'members'
    paginate_by = 50
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff_or_above():
            messages.error(request, 'You do not have permission to view this page.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(contact_number__icontains=search_query)
            )
        
        # Filter by sector
        sector = self.request.GET.get('sector')
        if sector:
            queryset = queryset.filter(sector=sector)
        
        # Filter by approval status
        approval = self.request.GET.get('approved')
        if approval == 'yes':
            queryset = queryset.filter(is_approved=True)
        elif approval == 'no':
            queryset = queryset.filter(is_approved=False)
        
        # Filter by municipality
        municipality = self.request.GET.get('municipality')
        if municipality:
            queryset = queryset.filter(address_municipality__icontains=municipality)
        
        return queryset.select_related('user', 'approved_by').order_by('-date_of_application')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '#FahanieCares Members'
        context['sector_choices'] = FahanieCaresMember.SECTOR_CHOICES
        context['total_members'] = FahanieCaresMember.objects.count()
        context['approved_members'] = FahanieCaresMember.objects.filter(is_approved=True).count()
        context['pending_members'] = FahanieCaresMember.objects.filter(is_approved=False).count()
        return context


class MemberDetailView(DetailView):
    """
    Staff view for viewing member details
    """
    model = FahanieCaresMember
    template_name = 'constituents/member_profile.html'
    context_object_name = 'member'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.object.first_name} {self.object.last_name} - Member Profile'
        return context


class MemberCreateView(CreateView):
    """
    Staff view for creating new members
    """
    model = FahanieCaresMember
    form_class = FahanieCaresMemberRegistrationForm
    template_name = 'constituents/member_registration.html'
    success_url = reverse_lazy('staff_member_list')
    
    def form_valid(self, form):
        # Staff can approve members immediately
        form.instance.is_approved = True
        form.instance.approved_by = self.request.user
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f'Member {self.object.first_name} {self.object.last_name} has been created successfully!'
        )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Member'
        context['is_staff_create'] = True
        return context