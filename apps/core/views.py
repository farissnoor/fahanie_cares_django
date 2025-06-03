from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from datetime import datetime
from apps.constituents.models import Constituent
from apps.referrals.models import ServiceCategory, Service
from apps.chapters.models import Chapter
from apps.services.models import ServiceProgram, MinistryProgram
from apps.communications.forms import ContactForm, PartnershipForm, DonationForm
from apps.communications.models import ContactFormSubmission, PartnershipSubmission, DonationSubmission

class HomePageView(TemplateView):
    """Home page view."""
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get featured services
        context['featured_services'] = Service.objects.filter(
            is_active=True,
            is_featured=True
        )[:6]
        
        # Get active chapters count
        context['active_chapters'] = Chapter.objects.filter(
            status='active'
        ).count()
        
        # Get service programs
        context['service_programs'] = ServiceProgram.objects.filter(
            status='active',
            published_at__isnull=False
        )[:3]
        
        # Sample impact stats for display
        context['impact_stats'] = {
            'constituents_served': 5000,
            'active_chapters': 25,
            'referrals_processed': 500,
            'community_programs': 30
        }
        
        # Get sample announcements for display
        context['announcements'] = [
            {
                'title': 'Food Sharing Program for Departing Pilgrims',
                'excerpt': 'Sharing food with those embarking on spiritual journeys is a deeply meaningful expression of community support and care. Providing modest yet meaningful refreshments to pilgrims.',
                'date': 'May 17, 2025',
                'category': 'Program',
                'image': 'pilgrims.jpg'
            },
            {
                'title': 'Turnover of Assistive Devices',
                'excerpt': 'The Office of MP Sittie Fahanie Uy-Oyod commits to supporting the welfare of Persons with Disabilities (PWDs) through the provision of essential assistive devices.',
                'date': 'May 16, 2025',
                'category': 'Event',
                'image': 'Devices.jpg'
            },
            {
                'title': 'Financial Assistance and Focus Group Discussion for Qualified Volunteer Teachers',
                'excerpt': 'The office of MP Uy-Oyod recognizes the challenges faced by Volunteer Teachers in the Bangsamoro region. Provide limited financial assistance to qualified volunteer teachers.',
                'date': 'May 26, 2025',
                'category': 'Event',
                'image': 'VTS.jpg'
            },
            {
                'title': 'New Health Services Partnership',
                'excerpt': 'A new partnership with the Ministry of Health expands healthcare access in remote areas.',
                'date': 'January 15, 2023',
                'category': 'News',
                'image': '' # Placeholder for now
            },
            {
                'title': 'Monthly Community Cleanup Drive',
                'excerpt': 'Join our volunteers for the monthly community cleanup drive in Datu Piang.',
                'date': 'January 20, 2023',
                'category': 'Event',
                'image': '' # Placeholder for now
            },
            {
                'title': 'New Education Bill Passes',
                'excerpt': 'MP Uy-Oyod\'s education bill passes, providing additional funding for rural schools.',
                'date': 'January 12, 2023',
                'category': 'Parliament',
                'image': '' # Placeholder for now
            }
        ]
        
        # Add contact form to context
        context['contact_form'] = ContactForm()
        
        return context
        
    def post(self, request, *args, **kwargs):
        # Process contact form submission from Home page
        contact_form = ContactForm(request.POST)
        
        if contact_form.is_valid():
            # Save the contact form submission
            submission = contact_form.save(commit=False)
            submission.form_source = 'home_page'
            submission.save()
            
            context = self.get_context_data(**kwargs)
            context['message'] = 'Thank you for your message. We will get back to you soon.'
            context['message_type'] = 'success'
            context['contact_form'] = ContactForm()  # Fresh form
            return render(request, self.template_name, context)
        else:
            # Form has errors
            context = self.get_context_data(**kwargs)
            context['contact_form'] = contact_form
            context['message'] = 'Please correct the errors below.'
            context['message_type'] = 'error'
            return render(request, self.template_name, context)

class MinistriesPPAsView(TemplateView):
    """Ministries and PPAs view."""
    template_name = 'core/ministries_ppas.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get ministry filter from URL parameter
        ministry_filter = self.request.GET.get('ministry')
        
        # Get all ministry programs (excluding deleted ones)
        ministry_programs = MinistryProgram.objects.filter(
            is_deleted=False,
            is_public=True
        ).order_by('ministry', '-created_at')
        
        # Filter by ministry if specified
        if ministry_filter:
            ministry_programs = ministry_programs.filter(ministry=ministry_filter)
        
        # Get ministry statistics
        ministry_stats = {}
        for ministry_code, ministry_name in MinistryProgram.MINISTRIES:
            count = MinistryProgram.objects.filter(
                ministry=ministry_code,
                is_deleted=False,
                is_public=True
            ).count()
            ministry_stats[ministry_code] = {
                'name': ministry_name,
                'code': ministry_code,
                'count': count,
                'description': self._get_ministry_description(ministry_code)
            }
        
        # Get featured programs
        featured_programs = MinistryProgram.objects.filter(
            is_featured=True,
            is_deleted=False,
            is_public=True
        )[:6]
        
        # Prepare ministry data for template
        ministries = []
        for ministry_code, ministry_data in ministry_stats.items():
            if ministry_data['count'] > 0:  # Only include ministries with programs
                ministries.append(ministry_data)
        
        # Prepare PPAS items for template
        ppas_items = []
        for program in ministry_programs[:12]:  # Limit to 12 for initial load
            # Format budget for display
            budget_display = ''
            if program.total_budget > 0:
                if program.total_budget >= 1000000000:  # Billions
                    budget_display = f"₱{program.total_budget / 1000000000:.1f}B"
                elif program.total_budget >= 1000000:  # Millions
                    budget_display = f"₱{program.total_budget / 1000000:.1f}M"
                elif program.total_budget >= 1000:  # Thousands
                    budget_display = f"₱{program.total_budget / 1000:.1f}K"
                else:
                    budget_display = f"₱{program.total_budget:,.0f}"
            
            ppas_items.append({
                'id': program.id,
                'title': program.title,
                'type': program.get_ppa_type_display(),
                'ministry': program.get_ministry_display(),
                'ministry_code': program.ministry,
                'description': program.description[:200] + '...' if len(program.description) > 200 else program.description,
                'location': program.geographic_coverage,
                'target': program.target_beneficiaries[:100] + '...' if len(program.target_beneficiaries) > 100 else program.target_beneficiaries,
                'timeline': f"{program.start_date.strftime('%b %Y')} - {program.end_date.strftime('%b %Y')}",
                'budget': program.total_budget,
                'budget_display': budget_display,
                'status': program.get_status_display(),
                'priority': program.get_priority_level_display(),
                'slug': program.slug
            })
        
        context.update({
            'ministries': ministries,
            'ppas_items': ppas_items,
            'featured_programs': featured_programs,
            'ministry_filter': ministry_filter,
            'total_programs': ministry_programs.count(),
            'ministry_stats': ministry_stats,
        })
        
        return context
    
    def _get_ministry_description(self, ministry_code):
        """Get description for each ministry."""
        descriptions = {
            'mssd': 'Leading social protection and welfare programs for vulnerable populations across BARMM.',
            'mafar': 'Promoting sustainable agriculture, fisheries, and agrarian reform for food security and economic growth.',
            'mtit': 'Driving economic development through trade promotion, industrial growth, and tourism development.',
            'mhe': 'Advancing higher education and technical skills development for the Bangsamoro people.',
            'mbasiced': 'Ensuring quality basic education and technical training for all learners in BARMM.',
            'moh': 'Providing comprehensive healthcare services and promoting public health across the region.',
            'mpwh': 'Building essential infrastructure and maintaining public works for regional development.',
            'motc': 'Developing transportation networks and communication systems for connectivity and growth.',
            'mei': 'Protecting the environment and promoting sustainable development and good governance.',
            'mle': 'Creating employment opportunities and protecting workers\' rights in BARMM.',
        }
        return descriptions.get(ministry_code, 'Ministry programs and services for the Bangsamoro people.')

class ProgramsView(TemplateView):
    """Programs view."""
    template_name = 'core/programs.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all programs
        context['programs'] = ServiceProgram.objects.filter(
            status='active'
        ).order_by('-start_date')
        
        return context

class MobileServiceView(View):
    """Mobile-optimized service view."""
    
    def get(self, request):
        # Detect if mobile device
        is_mobile = self.is_mobile_device(request)
        
        if is_mobile:
            return render(request, 'mobile/services.html')
        else:
            return redirect('services')
    
    def is_mobile_device(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        mobile_agents = ['android', 'iphone', 'ipad', 'mobile']
        return any(agent in user_agent for agent in mobile_agents)

class OfflineFormView(View):
    """Offline form for field registration."""
    
    def get(self, request):
        return render(request, 'mobile/offline_form.html')

@csrf_exempt
def mobile_sync_api(request):
    """API endpoint for syncing offline mobile data."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Create constituent record
        constituent = Constituent.objects.create(
            full_name=data.get('name'),
            contact_number=data.get('contact'),
            birth_date=data.get('birthdate'),
            municipality=data.get('municipality'),
            barangay=data.get('barangay'),
            complete_address=data.get('address'),
            created_by=request.user if request.user.is_authenticated else None
        )
        
        # Handle service request if provided
        if data.get('service_type'):
            # Create service request/referral
            from apps.referrals.models import Referral
            
            service = Service.objects.filter(
                service_type=data.get('service_type')
            ).first()
            
            if service:
                referral = Referral.objects.create(
                    constituent=constituent,
                    service=service,
                    description=data.get('description', ''),
                    urgency_level=data.get('urgency', 'normal'),
                    created_by=request.user if request.user.is_authenticated else None
                )
        
        return JsonResponse({
            'success': True,
            'constituent_id': constituent.id,
            'message': 'Data synchronized successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

def offline_page(request):
    """Offline fallback page."""
    return render(request, 'core/offline.html')

def service_worker(request):
    """Serve the service worker file."""
    sw_path = settings.STATICFILES_DIRS[0] / 'js' / 'service-worker.js'
    with open(sw_path, 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='application/javascript')

def manifest(request):
    """Serve the PWA manifest file."""
    manifest_path = settings.STATICFILES_DIRS[0] / 'manifest.json'
    with open(manifest_path, 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='application/json')

class AboutPageView(TemplateView):
    """About page view."""
    template_name = 'core/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add contact form with default subject for MP office contact
        context['contact_form'] = ContactForm(default_subject='feedback')
        return context
    
    def post(self, request, *args, **kwargs):
        # Process contact form submission from About Us page
        contact_form = ContactForm(request.POST, default_subject='feedback')
        
        if contact_form.is_valid():
            # Save the contact form submission
            submission = contact_form.save(commit=False)
            submission.form_source = 'about_page_mp_office'
            submission.save()
            
            context = self.get_context_data(**kwargs)
            context['message'] = 'Thank you for contacting MP Uy-Oyod\'s office. We will get back to you soon.'
            context['message_type'] = 'success'
            context['contact_form'] = ContactForm(default_subject='feedback')  # Fresh form
            return render(request, self.template_name, context)
        else:
            # Form has errors
            context = self.get_context_data(**kwargs)
            context['contact_form'] = contact_form
            context['message'] = 'Please correct the errors below.'
            context['message_type'] = 'error'
            return render(request, self.template_name, context)

class ChaptersPageView(TemplateView):
    """Chapters page view."""
    template_name = 'core/chapters.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get active chapters for display - only provincial and municipal chapters
        context['featured_chapters'] = Chapter.objects.filter(
            status='active', tier__in=['provincial', 'municipal']
        ).order_by('-created_at')[:3]  # Sort by newest and limit to 3
        
        # Get total chapters count by tier - only provincial and municipal chapters
        context['provincial_count'] = Chapter.objects.filter(tier='provincial').count()
        context['municipal_count'] = Chapter.objects.filter(tier='municipal').count()
        # Removed barangay_count and overseas_count as we're no longer showing them
        
        # Get total chapters count (only provincial and municipal)
        context['total_chapters'] = Chapter.objects.filter(
            status='active', tier__in=['provincial', 'municipal']
        ).count()
        
        # Add contact form with default subject for chapter inquiries
        context['contact_form'] = ContactForm(default_subject='chapter')
        
        return context
    
    def post(self, request, *args, **kwargs):
        # Process contact form submission from Chapters page
        contact_form = ContactForm(request.POST, default_subject='chapter')
        
        if contact_form.is_valid():
            # Save the contact form submission
            submission = contact_form.save(commit=False)
            submission.form_source = 'chapters_page_start_chapter'
            submission.save()
            
            context = self.get_context_data(**kwargs)
            context['message'] = 'Thank you for your chapter inquiry. Our team will contact you soon to discuss starting a chapter in your area.'
            context['message_type'] = 'success'
            context['contact_form'] = ContactForm(default_subject='chapter')  # Fresh form
            return render(request, self.template_name, context)
        else:
            # Form has errors
            context = self.get_context_data(**kwargs)
            context['contact_form'] = contact_form
            context['message'] = 'Please correct the errors below.'
            context['message_type'] = 'error'
            return render(request, self.template_name, context)

class ContactPageView(TemplateView):
    """Contact page view."""
    template_name = 'core/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add contact form for general inquiries
        context['contact_form'] = ContactForm()
        return context
    
    def post(self, request, *args, **kwargs):
        # Process contact form submission from Contact page
        contact_form = ContactForm(request.POST)
        
        if contact_form.is_valid():
            # Save the contact form submission
            submission = contact_form.save(commit=False)
            submission.form_source = 'contact_page'
            submission.save()
            
            context = self.get_context_data(**kwargs)
            context['message'] = 'Thank you for your message. We will get back to you soon.'
            context['message_type'] = 'success'
            context['contact_form'] = ContactForm()  # Fresh form
            return render(request, self.template_name, context)
        else:
            # Form has errors
            context = self.get_context_data(**kwargs)
            context['contact_form'] = contact_form
            context['message'] = 'Please correct the errors below.'
            context['message_type'] = 'error'
            return render(request, self.template_name, context)


class PartnerPageView(TemplateView):
    """Partnership page view."""
    template_name = "core/partner.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["partnership_form"] = PartnershipForm()
        return context
    
    def post(self, request, *args, **kwargs):
        partnership_form = PartnershipForm(request.POST)
        
        if partnership_form.is_valid():
            partnership_form.save()
            
            context = self.get_context_data(**kwargs)
            context["message"] = "Thank you for your partnership inquiry. Our team will review your application and get back to you soon."
            context["message_type"] = "success"
            context["partnership_form"] = PartnershipForm()  # Fresh form
            return render(request, self.template_name, context)
        else:
            context = self.get_context_data(**kwargs)
            context["partnership_form"] = partnership_form
            context["message"] = "Please correct the errors below."
            context["message_type"] = "error"
            return render(request, self.template_name, context)


class DonatePageView(TemplateView):
    """Donation page view."""
    template_name = "core/donate.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["donation_form"] = DonationForm()
        return context
    
    def post(self, request, *args, **kwargs):
        donation_form = DonationForm(request.POST)
        
        if donation_form.is_valid():
            donation_form.save()
            
            context = self.get_context_data(**kwargs)
            context["message"] = "Thank you for your donation inquiry. Our team will contact you to finalize the donation process."
            context["message_type"] = "success"
            context["donation_form"] = DonationForm()  # Fresh form
            return render(request, self.template_name, context)
        else:
            context = self.get_context_data(**kwargs)
            context["donation_form"] = donation_form
            context["message"] = "Please correct the errors below."
            context["message_type"] = "error"
            return render(request, self.template_name, context)
