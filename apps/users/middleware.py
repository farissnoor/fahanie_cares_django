"""
Security middleware for #FahanieCares.
"""

from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta

class SecurityHeadersMiddleware:
    """Adds security headers to all responses."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'same-origin'
        response['Permissions-Policy'] = "geolocation=(), microphone=(), camera=()"
        
        # Only add HSTS in production
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.notion.com;"
        )
        
        return response

class SessionSecurityMiddleware:
    """Manages session security and timeout."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Check for session timeout
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                last_activity_time = datetime.fromisoformat(last_activity)
                timeout_duration = timedelta(minutes=getattr(settings, 'SESSION_TIMEOUT_MINUTES', 30))
                
                if timezone.now() - last_activity_time > timeout_duration:
                    logout(request)
                    return redirect('login')
            
            # Update last activity
            request.session['last_activity'] = timezone.now().isoformat()
        
        response = self.get_response(request)
        return response

class MFAEnforcementMiddleware:
    """Enforces MFA for admin users."""
    
    MFA_EXEMPT_PATHS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/accounts/mfa/setup/',
        '/accounts/mfa/verify/',
        '/static/',
        '/media/',
        '/service-worker.js',
        '/manifest.json',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip MFA check for exempt paths
        for path in self.MFA_EXEMPT_PATHS:
            if request.path.startswith(path):
                return self.get_response(request)
        
        # Check if user requires MFA
        if request.user.is_authenticated and request.user.is_staff_or_above():
            # Check if MFA is verified for this session
            if not request.session.get('mfa_verified', False):
                # Check if user has MFA enabled
                if request.user.mfa_enabled:
                    # Store the intended destination
                    request.session['mfa_next'] = request.get_full_path()
                    return redirect('mfa_verify')
                else:
                    # Force MFA setup for admin users without it
                    return redirect('mfa_setup')
        
        response = self.get_response(request)
        return response

class RateLimitMiddleware:
    """Simple rate limiting middleware."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests = {}
    
    def __call__(self, request):
        # Simple in-memory rate limiting (use Redis in production)
        if request.path.startswith('/api/') or request.path == '/accounts/login/':
            ip = self.get_client_ip(request)
            now = timezone.now()
            
            # Clean old entries
            self.clean_old_entries(now)
            
            # Check rate limit
            if ip in self.requests:
                recent_requests = [req for req in self.requests[ip] if now - req < timedelta(minutes=1)]
                
                if len(recent_requests) >= getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60):
                    return HttpResponseForbidden("Rate limit exceeded")
                
                self.requests[ip] = recent_requests + [now]
            else:
                self.requests[ip] = [now]
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def clean_old_entries(self, now):
        """Clean old entries from memory."""
        cutoff = now - timedelta(minutes=5)
        for ip in list(self.requests.keys()):
            self.requests[ip] = [req for req in self.requests[ip] if req > cutoff]
            if not self.requests[ip]:
                del self.requests[ip]