"""
Security utilities and middleware for #FahanieCares.
"""

import secrets
import string
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
import pyotp
import hashlib
import hmac

User = get_user_model()

class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware to implement rate limiting for sensitive operations.
    """
    def process_request(self, request: HttpRequest) -> HttpResponse:
        # Skip rate limiting for staff and static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None
            
        if request.user.is_authenticated and request.user.is_staff_or_above():
            return None
        
        # Rate limit login attempts
        if request.path == reverse('login') and request.method == 'POST':
            ip_address = self.get_client_ip(request)
            cache_key = f'login_attempts_{ip_address}'
            attempts = cache.get(cache_key, 0)
            
            if attempts >= settings.MAX_LOGIN_ATTEMPTS:
                raise PermissionDenied("Too many login attempts. Please try again later.")
            
            # Increment attempts
            cache.set(cache_key, attempts + 1, settings.LOGIN_ATTEMPT_TIMEOUT)
        
        # Rate limit API requests
        if request.path.startswith('/api/'):
            ip_address = self.get_client_ip(request)
            cache_key = f'api_requests_{ip_address}'
            requests = cache.get(cache_key, 0)
            
            if requests >= settings.MAX_API_REQUESTS_PER_MINUTE:
                raise PermissionDenied("Rate limit exceeded. Please slow down your requests.")
            
            # Increment requests
            cache.set(cache_key, requests + 1, 60)  # 1 minute timeout
        
        return None
    
    def get_client_ip(self, request: HttpRequest) -> str:
        """Get the client's IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to responses.
    """
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.notion.com;"
        )
        
        # Other security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'same-origin'
        response['Feature-Policy'] = "geolocation 'none'; midi 'none'; camera 'none'; microphone 'none'"
        
        # Remove server header
        if 'Server' in response:
            del response['Server']
        
        return response

class MFAMiddleware(MiddlewareMixin):
    """
    Middleware to enforce MFA for admin users.
    """
    MFA_EXEMPT_PATHS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/mfa/setup/',
        '/accounts/mfa/verify/',
        '/static/',
        '/media/',
    ]
    
    def process_request(self, request: HttpRequest) -> HttpResponse:
        # Skip MFA check for exempt paths
        for path in self.MFA_EXEMPT_PATHS:
            if request.path.startswith(path):
                return None
        
        # Check if user requires MFA
        if request.user.is_authenticated and request.user.is_staff_or_above():
            # Check if MFA is verified for this session
            if not request.session.get('mfa_verified', False):
                # Check if user has MFA enabled
                if hasattr(request.user, 'mfa_enabled') and request.user.mfa_enabled:
                    return redirect('mfa_verify')
                else:
                    # Force MFA setup for admin users without it
                    return redirect('mfa_setup')
        
        return None

class MFAService:
    """
    Service for handling Multi-Factor Authentication.
    """
    @staticmethod
    def generate_secret():
        """Generate a new TOTP secret."""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_url(user, secret):
        """Generate QR code URL for setting up MFA."""
        issuer = "#FahanieCares"
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=user.email,
            issuer_name=issuer
        )
    
    @staticmethod
    def verify_token(secret, token):
        """Verify a TOTP token."""
        totp = pyotp.TOTP(secret)
        # Allow for time drift (30 seconds before/after)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def generate_backup_codes(count=10):
        """Generate backup codes for recovery."""
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            codes.append(code)
        return codes

class PasswordStrengthValidator:
    """
    Validate password strength requirements.
    """
    def __init__(self, min_length=12):
        self.min_length = min_length
    
    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValueError(f"Password must be at least {self.min_length} characters long.")
        
        # Check for character diversity
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in string.punctuation for c in password)
        
        if not (has_lower and has_upper and has_digit and has_special):
            raise ValueError(
                "Password must include lowercase, uppercase, digits, and special characters."
            )
        
        # Check for common patterns
        common_patterns = [
            'password', 'qwerty', '123456', 'admin', 'letmein',
            'welcome', 'monkey', 'dragon', 'master', 'sunshine'
        ]
        
        password_lower = password.lower()
        for pattern in common_patterns:
            if pattern in password_lower:
                raise ValueError("Password contains common patterns. Please choose a stronger password.")
        
        return True
    
    def get_help_text(self):
        return (
            f"Your password must be at least {self.min_length} characters long and include "
            "uppercase letters, lowercase letters, numbers, and special characters."
        )

class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Middleware to enhance session security.
    """
    def process_request(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            # Check session timeout
            last_activity = request.session.get('last_activity')
            if last_activity:
                last_activity_time = datetime.fromisoformat(last_activity)
                if datetime.now() - last_activity_time > timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES):
                    request.session.flush()
                    return redirect('login')
            
            # Update last activity
            request.session['last_activity'] = datetime.now().isoformat()
            
            # Check for session hijacking
            session_hash = self.get_session_hash(request)
            stored_hash = request.session.get('session_hash')
            
            if stored_hash and stored_hash != session_hash:
                request.session.flush()
                return redirect('login')
            
            request.session['session_hash'] = session_hash
        
        return None
    
    def get_session_hash(self, request: HttpRequest) -> str:
        """Generate a hash based on session-specific data."""
        data = f"{request.META.get('HTTP_USER_AGENT', '')}{request.META.get('REMOTE_ADDR', '')}"
        return hashlib.sha256(data.encode()).hexdigest()

class CSRFTokenGenerator:
    """
    Enhanced CSRF token generator.
    """
    @staticmethod
    def generate_token(session_key: str) -> str:
        """Generate a CSRF token tied to the session."""
        secret = settings.SECRET_KEY
        timestamp = str(int(datetime.now().timestamp()))
        
        # Create HMAC signature
        message = f"{session_key}:{timestamp}"
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{timestamp}:{signature}"
    
    @staticmethod
    def verify_token(token: str, session_key: str, max_age: int = 3600) -> bool:
        """Verify a CSRF token."""
        try:
            timestamp, signature = token.split(':')
            
            # Check age
            token_time = int(timestamp)
            current_time = int(datetime.now().timestamp())
            
            if current_time - token_time > max_age:
                return False
            
            # Verify signature
            expected_signature = hmac.new(
                settings.SECRET_KEY.encode(),
                f"{session_key}:{timestamp}".encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        
        except (ValueError, AttributeError):
            return False

# Custom authentication backend with security enhancements
class SecureAuthBackend(ModelBackend):
    """
    Enhanced authentication backend with security features.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Get IP address for rate limiting
        ip_address = request.META.get('REMOTE_ADDR') if request else None
        
        # Check if account is locked
        if ip_address:
            lock_key = f'account_locked_{username}'
            if cache.get(lock_key):
                return None
        
        # Perform authentication
        user = super().authenticate(request, username=username, password=password, **kwargs)
        
        if user is None and ip_address:
            # Track failed attempts
            fail_key = f'failed_login_{username}'
            failures = cache.get(fail_key, 0) + 1
            cache.set(fail_key, failures, 3600)  # 1 hour
            
            # Lock account after too many failures
            if failures >= 5:
                cache.set(lock_key, True, 900)  # 15 minutes
        
        elif user is not None and ip_address:
            # Clear failed attempts on successful login
            cache.delete(f'failed_login_{username}')
            
            # Log successful login
            self.log_login(user, ip_address)
        
        return user
    
    def log_login(self, user, ip_address):
        """Log successful login attempts."""
        # This could be extended to save to database or send to monitoring service
        cache.set(f'last_login_{user.id}', {
            'ip': ip_address,
            'timestamp': datetime.now().isoformat()
        }, 86400)  # 24 hours