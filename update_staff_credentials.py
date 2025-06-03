#!/usr/bin/env python3
"""
Update staff_login_credentials.txt with all current staff user accounts.
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append('/Users/macbookpro/Documents/fahanie-cares/fahanie_cares_django')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.staff.models import Staff

User = get_user_model()

def generate_password(name):
    """Generate password from first name + 2024!"""
    first_name = name.strip().split()[0]
    return f"{first_name}2024!"

def get_staff_credentials():
    """Get all staff user credentials"""
    staff_users = []
    
    # Get all users who have staff profiles
    users_with_staff = User.objects.filter(staff_profile__isnull=False).select_related('staff_profile')
    
    # Also include users who don't have staff profiles but seem to be staff based on their details
    potential_staff_users = User.objects.filter(
        models.Q(is_staff=True) |
        models.Q(email__icontains='fahanie') |
        models.Q(username__in=['atty.u', 'farissnoor.e', 'mae.l', 'rohamiah.i', 
                              'sherjan.u', 'tuhami.a', 'jamin.t', 'mokadafy.e', 
                              'saud.g', 'reah.l', 'nasruddin.o'])
    ).exclude(username__in=['admin', 'member_demo', 'constituent_demo', 'staff_demo'])
    
    all_staff_users = (users_with_staff | potential_staff_users).distinct().order_by('first_name', 'last_name')
    
    for user in all_staff_users:
        name = user.get_full_name() or f"{user.first_name} {user.last_name}".strip()
        if not name:
            name = user.username.replace('.', ' ').title()
        
        # Get position and division from staff profile if available
        position = "Staff"
        division = "MP Uy-Oyod's Office"
        
        if hasattr(user, 'staff_profile') and user.staff_profile:
            staff = user.staff_profile
            position = staff.position or "Staff"
            division_mapping = {
                'legislative_affairs': 'Legislative Affairs',
                'administrative_affairs': 'Administrative Affairs', 
                'communications': 'Communications',
                'mp_office': "MP Uy-Oyod's Office",
                'it_unit': 'IT Unit',
            }
            division = division_mapping.get(staff.division, staff.division or "MP Uy-Oyod's Office")
        
        # Determine password
        password = "Password already set"
        if user.username in ['john.d', 'jane.s', 'maria.s', 'atty.u', 'farissnoor.e']:
            password = generate_password(name)
        elif user.username in ['sherjan.u', 'tuhami.a', 'jamin.t', 'mokadafy.e', 'saud.g', 'reah.l', 'nasruddin.o']:
            password = generate_password(name)
        
        staff_users.append({
            'name': name,
            'position': position,
            'division': division,
            'username': user.username,
            'password': password,
            'email': user.email
        })
    
    return staff_users

def update_credentials_file():
    """Update the staff_login_credentials.txt file"""
    staff_credentials = get_staff_credentials()
    
    content = "#FahanieCares Staff Login Credentials\n"
    content += "=" * 60 + "\n\n"
    
    for staff in staff_credentials:
        content += f"Name: {staff['name']}\n"
        content += f"Position: {staff['position']}\n"
        content += f"Division: {staff['division']}\n"
        content += f"Username: {staff['username']}\n"
        content += f"Password: {staff['password']}\n"
        content += f"Email: {staff['email']}\n"
        content += "-" * 40 + "\n"
    
    content += "\nAccess URLs:\n"
    content += "Staff Portal: http://localhost:8000/staff/\n"
    content += "Django Admin: http://localhost:8000/admin/\n"
    content += "Login Page: http://localhost:8000/accounts/login/\n\n"
    content += "Notes:\n"
    content += "- New users should change their password on first login\n"
    content += "- All staff have Django admin access\n"
    content += "- Contact IT for password resets\n"
    
    with open('staff_login_credentials.txt', 'w') as f:
        f.write(content)
    
    print(f"✅ Updated staff_login_credentials.txt with {len(staff_credentials)} staff members")
    print("\nStaff included:")
    for staff in staff_credentials:
        print(f"  - {staff['name']} ({staff['username']})")

if __name__ == '__main__':
    # Add Django Q import
    from django.db import models
    update_credentials_file()