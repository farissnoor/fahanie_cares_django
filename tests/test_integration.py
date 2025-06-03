"""
Integration tests for #FahanieCares system.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from apps.constituents.models import Constituent
from apps.referrals.models import Service, Referral
from apps.chapters.models import Chapter, ChapterMembership
from apps.services.models import ServiceProgram, ServiceApplication

User = get_user_model()

class ServiceReferralIntegrationTest(TestCase):
    """Test the complete service referral flow."""
    
    def setUp(self):
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='Test@Pass123!',
            user_type='constituent'
        )
        
        # Create constituent profile
        self.constituent = Constituent.objects.create(
            user=self.user,
            full_name='Test User',
            contact_number='12345678',
            municipality='Test City'
        )
        
        # Create test service
        self.service = Service.objects.create(
            name='Medical Assistance',
            description='Healthcare support',
            category_id=1,
            is_active=True
        )
    
    @patch('utils.notion.client.NotionService')
    def test_complete_referral_flow(self, mock_notion):
        """Test creating and tracking a referral."""
        # Setup mock
        mock_notion_instance = mock_notion.return_value
        mock_notion_instance.create_page.return_value = {'id': 'notion123'}
        
        # Login
        self.client.login(username='testuser', password='Test@Pass123!')
        
        # Create referral
        response = self.client.post(reverse('create_referral'), {
            'service': self.service.id,
            'description': 'Need medical help',
            'urgency': 'high',
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Check referral was created
        referral = Referral.objects.get(constituent=self.constituent)
        self.assertEqual(referral.service, self.service)
        self.assertEqual(referral.urgency, 'high')
        
        # Check Notion was called
        mock_notion_instance.create_page.assert_called_once()

class ChapterMembershipIntegrationTest(TestCase):
    """Test chapter membership flow."""
    
    def setUp(self):
        self.client = Client()
        
        # Create test users
        self.member = User.objects.create_user(
            username='member',
            email='member@test.com',
            password='Test@Pass123!',
            user_type='constituent'
        )
        
        self.coordinator = User.objects.create_user(
            username='coordinator',
            email='coord@test.com',
            password='Test@Pass123!',
            user_type='coordinator'
        )
        
        # Create chapter
        self.chapter = Chapter.objects.create(
            name='Test Chapter',
            municipality='Test City',
            coordinator=self.coordinator,
            status='active'
        )
    
    def test_membership_application_flow(self):
        """Test applying for chapter membership."""
        # Login as member
        self.client.login(username='member', password='Test@Pass123!')
        
        # Apply for membership
        response = self.client.post(
            reverse('chapter_join', args=[self.chapter.slug]),
            {
                'is_volunteer': True,
                'volunteer_skills': 'Teaching, organizing events',
                'availability': 'Weekends',
                'notes': 'Excited to join!'
            }
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Check membership was created
        membership = ChapterMembership.objects.get(
            user=self.member,
            chapter=self.chapter
        )
        self.assertEqual(membership.status, 'pending')
        self.assertTrue(membership.is_volunteer)
        
        # Login as coordinator to approve
        self.client.login(username='coordinator', password='Test@Pass123!')
        
        # Approve membership (this would normally be through admin interface)
        membership.approve(self.coordinator)
        
        # Check member ID was generated
        self.assertIsNotNone(membership.membership_number)
        self.assertTrue(membership.membership_number.startswith('FCM-'))

class MobileOfflineIntegrationTest(TestCase):
    """Test mobile offline functionality."""
    
    def setUp(self):
        self.client = Client()
        self.client.defaults['HTTP_USER_AGENT'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
    
    def test_offline_form_submission(self):
        """Test offline form data sync."""
        data = {
            'name': 'Offline User',
            'contact': '9876543210',
            'municipality': 'Remote Town',
            'service_type': 'emergency',
            'description': 'Need emergency assistance',
            'urgency': 'urgent'
        }
        
        response = self.client.post('/api/mobile/sync/', data, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # Check constituent was created
        constituent = Constituent.objects.get(full_name='Offline User')
        self.assertEqual(constituent.municipality, 'Remote Town')

class SecurityIntegrationTest(TestCase):
    """Test security features."""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='Test@Pass123!',
            user_type='staff'
        )
    
    def test_mfa_enforcement(self):
        """Test MFA is enforced for staff users."""
        # Login
        self.client.login(username='staff', password='Test@Pass123!')
        
        # Try to access protected page
        response = self.client.get(reverse('staff_dashboard'))
        
        # Should redirect to MFA setup
        self.assertEqual(response.status_code, 302)
        self.assertIn('mfa/setup', response.url)
    
    def test_session_timeout(self):
        """Test session timeout functionality."""
        from datetime import datetime, timedelta
        
        # Login
        self.client.login(username='staff', password='Test@Pass123!')
        
        # Simulate old session
        session = self.client.session
        old_time = datetime.now() - timedelta(hours=1)
        session['last_activity'] = old_time.isoformat()
        session.save()
        
        # Try to access page
        response = self.client.get(reverse('constituent_dashboard'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

class PerformanceIntegrationTest(TestCase):
    """Test system performance."""
    
    def setUp(self):
        # Create test data
        for i in range(100):
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='Test@Pass123!'
            )
    
    def test_user_list_performance(self):
        """Test performance of user listing."""
        import time
        
        start_time = time.time()
        response = self.client.get('/admin/users/user/')
        end_time = time.time()
        
        # Should complete within reasonable time
        self.assertLess(end_time - start_time, 2.0)
        self.assertEqual(response.status_code, 302)  # Redirect to login

class EndToEndTest(TestCase):
    """Test complete user journeys."""
    
    def setUp(self):
        self.client = Client()
    
    def test_constituent_journey(self):
        """Test complete constituent journey from registration to service request."""
        # Register
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'Test@Pass123!',
            'password2': 'Test@Pass123!',
            'first_name': 'New',
            'last_name': 'User',
            'user_type': 'constituent'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Login
        self.client.login(username='newuser', password='Test@Pass123!')
        
        # Complete profile
        response = self.client.post(reverse('constituent_profile'), {
            'full_name': 'New User',
            'contact_number': '1234567890',
            'municipality': 'Test City',
            'address': '123 Test St'
        })
        
        # Request service
        service = Service.objects.create(
            name='Test Service',
            description='Test',
            category_id=1,
            is_active=True
        )
        
        response = self.client.post(reverse('create_referral'), {
            'service': service.id,
            'description': 'Need help',
            'urgency': 'normal'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Check referral exists
        constituent = Constituent.objects.get(user__username='newuser')
        referral = Referral.objects.get(constituent=constituent)
        self.assertEqual(referral.service, service)