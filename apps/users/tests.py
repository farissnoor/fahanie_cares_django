from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .security import MFAService, PasswordStrengthValidator
import pyotp

User = get_user_model()

class MFATestCase(TestCase):
    """Test cases for MFA functionality."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='teststaff',
            email='staff@test.com',
            password='Test@Pass123!',
            user_type='staff'
        )
    
    def test_mfa_required_for_staff(self):
        """Test that MFA is required for staff users."""
        self.client.login(username='teststaff', password='Test@Pass123!')
        response = self.client.get(reverse('constituent_dashboard'))
        
        # Should redirect to MFA setup
        self.assertEqual(response.status_code, 302)
        self.assertIn('mfa/setup', response.url)
    
    def test_mfa_setup_generates_secret(self):
        """Test MFA setup generates a valid secret."""
        self.client.login(username='teststaff', password='Test@Pass123!')
        response = self.client.get(reverse('mfa_setup'))
        
        # Check session has secret
        session = self.client.session
        self.assertIn('mfa_secret', session)
        
        # Verify secret is valid
        secret = session['mfa_secret']
        self.assertEqual(len(secret), 32)
    
    def test_mfa_token_verification(self):
        """Test MFA token verification."""
        secret = MFAService.generate_secret()
        totp = pyotp.TOTP(secret)
        
        # Test valid token
        valid_token = totp.now()
        self.assertTrue(MFAService.verify_token(secret, valid_token))
        
        # Test invalid token
        self.assertFalse(MFAService.verify_token(secret, '000000'))
    
    def test_backup_codes_generation(self):
        """Test backup codes generation."""
        codes = MFAService.generate_backup_codes()
        
        self.assertEqual(len(codes), 10)
        for code in codes:
            self.assertEqual(len(code), 8)
            self.assertTrue(code.isalnum())

class PasswordStrengthTestCase(TestCase):
    """Test cases for password strength validation."""
    
    def setUp(self):
        self.validator = PasswordStrengthValidator()
    
    def test_strong_password(self):
        """Test that strong passwords pass validation."""
        strong_passwords = [
            'StrongPass123!',
            'Complex@Pass456',
            'MySecure#Pass789'
        ]
        
        for password in strong_passwords:
            self.assertTrue(self.validator.validate(password))
    
    def test_weak_passwords(self):
        """Test that weak passwords fail validation."""
        weak_passwords = [
            'short',  # Too short
            'alllowercase123!',  # No uppercase
            'ALLUPPERCASE123!',  # No lowercase
            'NoNumbers!',  # No digits
            'NoSpecialChars123',  # No special characters
            'Password123!',  # Contains common pattern
        ]
        
        for password in weak_passwords:
            with self.assertRaises(ValueError):
                self.validator.validate(password)

class SecurityHeadersTestCase(TestCase):
    """Test cases for security headers."""
    
    def test_security_headers_present(self):
        """Test that security headers are present in responses."""
        response = self.client.get('/')
        
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-XSS-Protection'], '1; mode=block')
        self.assertIn('Content-Security-Policy', response)

class SessionSecurityTestCase(TestCase):
    """Test cases for session security."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='Test@Pass123!'
        )
    
    def test_session_timeout(self):
        """Test session timeout functionality."""
        self.client.login(username='testuser', password='Test@Pass123!')
        
        # Simulate expired session
        session = self.client.session
        past_time = timezone.now() - timedelta(hours=1)
        session['last_activity'] = past_time.isoformat()
        session.save()
        
        response = self.client.get(reverse('constituent_dashboard'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)