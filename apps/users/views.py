from django.shortcuts import render, redirect
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserRegistrationForm
from apps.constituents.member_forms import FahanieCaresMemberRegistrationForm
from utils.notion.client import NotionService
from django.conf import settings
from utils.notion.database import format_title, format_rich_text, format_phone_number, format_email, format_select, format_checkbox

class CustomLoginView(LoginView):
    """
    Custom login view for #FahanieCares.
    """
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        # Add custom login logic here if needed
        return super().form_valid(form)

class UserRegistrationView(CreateView):
    """
    User registration view for #FahanieCares.
    Creates a new user and also adds them to the Notion members database.
    """
    template_name = 'constituents/member_registration.html'
    form_class = FahanieCaresMemberRegistrationForm
    success_url = reverse_lazy('registration_success')
    
    def form_valid(self, form):
        # The form's save method handles both User and FahanieCaresMember creation
        response = super().form_valid(form)
        
        # Show success message
        messages.success(
            self.request, 
            'Your #FahanieCares membership application has been submitted successfully! '
            'You will receive an email once your application is approved.'
        )
        
        return response

class RegistrationSuccessView(TemplateView):
    """
    Success page after registration.
    """
    template_name = 'constituents/registration_success.html'
    

class MemberRegistrationView(LoginRequiredMixin, CreateView):
    """
    View for upgrading a constituent to a member.
    Only accessible to authenticated users who are not already members.
    """
    template_name = 'users/member_registration.html'
    form_class = UserRegistrationForm  # We'll reuse the same form
    success_url = reverse_lazy('home')
    login_url = '/accounts/login/'
    
    def get_initial(self):
        # Pre-fill the form with the user's existing data
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            user = self.request.user
            initial.update({
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone_number': user.phone_number,
                'address': user.address,
                'municipality': user.municipality,
            })
        return initial
    
    def form_valid(self, form):
        # Update the existing user instead of creating a new one
        user = self.request.user
        user.user_type = 'member'  # Upgrade to member
        
        # Update other fields from the form
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.email = form.cleaned_data['email']
        user.phone_number = form.cleaned_data['phone_number']
        user.address = form.cleaned_data['address']
        user.municipality = form.cleaned_data['municipality']
        user.save()
        
        # Add the user to Notion database (when set up)
        try:
            notion_service = NotionService()
            
            # Only try to create or update Notion record if API key is configured
            if settings.NOTION_API_KEY and settings.NOTION_MEMBER_DATABASE:
                # If user already has a Notion ID, update the record
                if user.notion_id:
                    member_properties = {
                        'Name': format_title(f"{user.first_name} {user.last_name}"),
                        'Email': format_email(user.email),
                        'Phone': format_phone_number(user.phone_number),
                        'Address': format_rich_text(user.address),
                        'Municipality': format_rich_text(user.municipality),
                        'User Type': format_select(user.user_type),
                    }
                    notion_service.update_page(user.notion_id, member_properties)
                else:
                    # Create a record in the Members database
                    member_properties = {
                        'Name': format_title(f"{user.first_name} {user.last_name}"),
                        'Email': format_email(user.email),
                        'Phone': format_phone_number(user.phone_number),
                        'Address': format_rich_text(user.address),
                        'Municipality': format_rich_text(user.municipality),
                        'User Type': format_select(user.user_type),
                        'Is Approved': format_checkbox(user.is_approved),
                        'User ID': format_rich_text(str(user.id)),
                    }
                    
                    notion_page = notion_service.create_page(
                        database_id=settings.NOTION_MEMBER_DATABASE,
                        properties=member_properties
                    )
                    
                    # Save the Notion ID back to the user
                    user.notion_id = notion_page['id']
                    user.save(update_fields=['notion_id'])
        except Exception as e:
            # Log the error but don't prevent user upgrade
            print(f"Error updating Notion record: {str(e)}")
        
        # Show success message
        messages.success(self.request, "Congratulations! You are now a registered #FahanieCares member.")
        
        return redirect(self.success_url)