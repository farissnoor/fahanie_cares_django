#!/usr/bin/env python3
"""
Create user accounts for remaining staff members from Notion database
who don't currently have Django user accounts.
"""

import os
import sys
import django
from datetime import datetime
import uuid

# Add the project root to Python path
sys.path.append('/Users/macbookpro/Documents/fahanie-cares/fahanie_cares_django')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.staff.models import Staff

User = get_user_model()

# Staff members from Notion database who need user accounts
remaining_staff = [
    {
        'name': 'Sherjan Uy',
        'position': 'Staff',
        'division': "MP Uy-Oyod's Office",
        'email': 'sherjan.uy@fahanie.gov.ph'
    },
    {
        'name': 'Tuhami P. Ali',
        'position': 'Staff',
        'division': "MP Uy-Oyod's Office", 
        'email': 'tuhami.ali@fahanie.gov.ph'
    },
    {
        'name': 'Jamin U. Tatua',
        'position': 'Staff',
        'division': "MP Uy-Oyod's Office",
        'email': 'jamin.tatua@fahanie.gov.ph'
    },
    {
        'name': 'Mokadafy I. Ebus',
        'position': 'Staff',
        'division': "MP Uy-Oyod's Office",
        'email': 'mokadafy.ebus@fahanie.gov.ph'
    },
    {
        'name': 'Saud U. Guiamelon',
        'position': 'Staff', 
        'division': "MP Uy-Oyod's Office",
        'email': 'saud.guiamelon@fahanie.gov.ph'
    },
    {
        'name': 'Reah J. Lauban',
        'position': 'Staff',
        'division': "MP Uy-Oyod's Office",
        'email': 'reah.lauban@fahanie.gov.ph'
    },
    {
        'name': 'Nasruddin G. Oyod',
        'position': 'Staff',
        'division': "MP Uy-Oyod's Office",
        'email': 'nasruddin.oyod@fahanie.gov.ph'
    }
]

def generate_username(name):
    """Generate username from name (firstname.lastinitial)"""
    parts = name.strip().split()
    if len(parts) >= 2:
        first_name = parts[0].lower()
        last_initial = parts[-1][0].lower()
        username = f"{first_name}.{last_initial}"
    else:
        username = name.lower().replace(' ', '.')
    
    return username

def generate_password(name):
    """Generate password from first name + 2024!"""
    first_name = name.strip().split()[0]
    return f"{first_name}2024!"

def create_user_and_staff(staff_data):
    """Create both User and Staff records"""
    name = staff_data['name']
    username = generate_username(name)
    password = generate_password(name)
    email = staff_data['email']
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"User {username} already exists, skipping...")
        return None
        
    if User.objects.filter(email=email).exists():
        print(f"User with email {email} already exists, skipping...")
        return None
    
    try:
        # Parse name parts
        name_parts = name.strip().split()
        first_name = name_parts[0] if name_parts else name
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        
        # Create User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_active=True
        )
        
        # Create Staff profile
        staff = Staff.objects.create(
            user=user,
            notion_id=str(uuid.uuid4()),  # Generate unique notion_id
            full_name=name,
            position=staff_data['position'],
            division='mp_office',  # Use the choice key instead
            email=email,
            employment_status='coterminous',  # Use a valid choice
            date_hired=datetime.now().date(),
            is_active=True
        )
        
        print(f"✅ Created user and staff profile for: {name}")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Email: {email}")
        print()
        
        return {
            'name': name,
            'position': staff_data['position'],
            'division': staff_data['division'],
            'username': username,
            'password': password,
            'email': email
        }
        
    except Exception as e:
        print(f"❌ Error creating user for {name}: {str(e)}")
        return None

def main():
    print("Creating user accounts for remaining staff members...")
    print("=" * 60)
    
    created_users = []
    
    for staff_data in remaining_staff:
        result = create_user_and_staff(staff_data)
        if result:
            created_users.append(result)
    
    print(f"\n✅ Successfully created {len(created_users)} user accounts")
    
    if created_users:
        print("\nNew user credentials:")
        print("-" * 40)
        for user in created_users:
            print(f"Name: {user['name']}")
            print(f"Username: {user['username']}")
            print(f"Password: {user['password']}")
            print(f"Email: {user['email']}")
            print("-" * 40)
    
    return created_users

if __name__ == '__main__':
    created_users = main()