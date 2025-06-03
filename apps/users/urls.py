from django.urls import path
from django.contrib.auth.views import LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.views.generic import RedirectView
from .views import CustomLoginView, UserRegistrationView, RegistrationSuccessView, MemberRegistrationView
from . import mfa_views

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('register/success/', RegistrationSuccessView.as_view(), name='registration_success'),
    path('register/member/', MemberRegistrationView.as_view(), name='register_member'),
    
    # Profile redirect - will check if user has FahanieCares member profile
    path('profile/', RedirectView.as_view(pattern_name='member_profile', permanent=False), name='profile'),
    
    # Password reset URLs
    path('password-reset/', PasswordResetView.as_view(template_name='users/password_reset.html'), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), name='password_reset_complete'),
    
    # MFA URLs
    path('mfa/setup/', mfa_views.mfa_setup, name='mfa_setup'),
    path('mfa/verify/', mfa_views.mfa_verify, name='mfa_verify'),
    path('mfa/backup-codes/', mfa_views.regenerate_backup_codes, name='regenerate_backup_codes'),
    path('security/', mfa_views.user_security_settings, name='user_security_settings'),
]