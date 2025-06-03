#!/usr/bin/env python
"""
Script to create user accounts for staff members and add sample staff data.
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.append('/Users/macbookpro/Documents/fahanie-cares/fahanie_cares_django')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.staff.models import Staff
import re
from datetime import date

User = get_user_model()

# Additional staff data to create
ADDITIONAL_STAFF = [
    {
        'full_name': 'Mae Anne C. Lidasan',
        'position': 'Administrative Coordinator',
        'email': 'maeanne.lidasan@fahanie.gov.ph',
        'phone_number': '09366186579',
        'address': 'RH IV, Cotabato City',
        'division': 'administrative_affairs',
        'employment_status': 'contractual',
        'office': 'main_office',
        'date_hired': date(2025, 3, 24),
    },
    {
        'full_name': 'Farissnoor Edza',
        'position': 'IT Staff',
        'email': 'farissnoor.edza@fahanie.gov.ph',
        'phone_number': '09302574952',
        'address': 'RH IV, Cotabato City',
        'division': 'it_unit',
        'employment_status': 'contractual',
        'office': 'main_office',
        'date_hired': date(2025, 3, 24),
        'duties_responsibilities': '''1. Assist in the development and maintenance of the #FahanieCares Portal / website.
2. Assist in the development and maintenance of the Notion Workspace of the Office.
3. Provide technical support and training on the IT needs of the Office.
4. Provide support to the Public Information and Media Affairs (PIMA)
5. Perform Other Duties and Responsibilities as Instructed.''',
        'staff_workflow': '''1. Check and update Notion (2h).
2. Develop website (3-4h).
3. Assist in PIMA work (1-2h).
4. Other Tasks / Professional Development (1h).'''
    },
    {
        'full_name': 'Atty. Sittie Fahanie S. Uy-Oyod',
        'position': 'Member of Parliament',
        'email': 'mp.uyoyod@fahanie.gov.ph',
        'phone_number': '09123456789',
        'address': 'RH IV, Cotabato City',
        'division': 'mp_office',
        'employment_status': 'coterminous',
        'office': 'main_office',
        'date_hired': date(2022, 6, 30),
        'duties_responsibilities': 'Member of Parliament representing RH IV, Cotabato City. Legislative work, constituent services, policy development.',
        'staff_workflow': 'Parliamentary sessions, constituent services, policy development, public engagements'
    },
    {
        'full_name': 'John Doe',
        'position': 'Legislative Assistant',
        'email': 'john.doe@fahanie.gov.ph',
        'phone_number': '09234567890',
        'address': 'RH IV, Cotabato City',
        'division': 'legislative_affairs',
        'employment_status': 'contractual',
        'office': 'main_office',
        'date_hired': date(2024, 1, 15),
    },
    {
        'full_name': 'Jane Smith',
        'position': 'Communications Officer',
        'email': 'jane.smith@fahanie.gov.ph',
        'phone_number': '09345678901',
        'address': 'RH IV, Cotabato City',
        'division': 'communications',
        'employment_status': 'consultant',
        'office': 'main_office',
        'date_hired': date(2024, 2, 1),
    },
    {
        'full_name': 'Maria Santos',
        'position': 'Administrative Officer',
        'email': 'maria.santos@fahanie.gov.ph',
        'phone_number': '09456789012',
        'address': 'RH IV, Cotabato City',
        'division': 'administrative_affairs',
        'employment_status': 'contractual',
        'office': 'main_office',
        'date_hired': date(2024, 3, 1),
    }
]

def create_username(full_name):
    """Generate a username from full name."""
    # Remove special characters and convert to lowercase
    clean_name = re.sub(r'[^a-zA-Z\s]', '', full_name)
    # Split into parts and take first name + last initial
    parts = clean_name.strip().split()
    if len(parts) >= 2:
        username = f"{parts[0].lower()}.{parts[-1][0].lower()}"
    else:
        username = parts[0].lower() if parts else "staff"
    
    # Ensure uniqueness
    base_username = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    return username

def create_default_password(full_name):
    """Generate a default password from full name."""
    # Take first name + "2024"
    parts = full_name.strip().split()
    first_name = parts[0] if parts else "staff"
    # Capitalize first letter and remove special chars
    clean_first_name = re.sub(r'[^a-zA-Z]', '', first_name)
    password = clean_first_name.capitalize() + "2024!"
    return password

def create_user_for_staff(staff):
    """Create a user account for a staff member."""
    if staff.user:
        return None  # Already has a user
    
    # Generate username and password
    username = create_username(staff.full_name)
    password = create_default_password(staff.full_name)
    
    # Extract name parts for user creation
    name_parts = staff.full_name.strip().split()
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
    
    # Create user account
    user = User.objects.create_user(
        username=username,
        email=staff.email or f"{username}@fahanie.gov.ph",
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_staff=True,  # Give staff permissions
        is_active=True
    )
    
    # Link user to staff profile
    staff.user = user
    staff.save()
    
    return {
        'staff': staff,
        'username': username,
        'password': password,
        'email': user.email
    }

def main():
    """Main execution function."""
    print("🚀 Creating Staff Members and User Accounts")
    print("=" * 50)
    print()
    
    created_users = []
    
    # First, create user accounts for existing staff without users
    print("📋 Checking existing staff for missing user accounts...")
    existing_staff = Staff.objects.all()
    
    for staff in existing_staff:
        if not staff.user:
            user_data = create_user_for_staff(staff)
            if user_data:
                created_users.append(user_data)
                print(f"✅ Created user for existing staff: {staff.full_name} -> {user_data['username']}")
        else:
            print(f"⏭️  {staff.full_name} already has user: {staff.user.username}")
    
    print()
    print("🆕 Creating additional staff members...")
    
    # Create additional staff members
    for staff_data in ADDITIONAL_STAFF:
        full_name = staff_data['full_name']
        
        # Check if staff already exists
        if Staff.objects.filter(full_name=full_name).exists():
            print(f"⏭️  Staff member {full_name} already exists")
            continue
        
        # Create new staff member
        staff = Staff.objects.create(**staff_data)
        print(f"✅ Created staff member: {full_name}")
        
        # Create user account
        user_data = create_user_for_staff(staff)
        if user_data:
            created_users.append(user_data)
            print(f"✅ Created user account: {user_data['username']}")
    
    print()
    print("=" * 80)
    print("📋 STAFF USER CREDENTIALS SUMMARY")
    print("=" * 80)
    
    if created_users:
        print(f"\n🎉 Successfully created {len(created_users)} user accounts:")
        print()
        
        # Table header
        print(f"{'FULL NAME':<30} {'USERNAME':<20} {'PASSWORD':<15} {'POSITION':<25}")
        print("-" * 90)
        
        # User rows
        for user_data in created_users:
            staff = user_data['staff']
            username = user_data['username']
            password = user_data['password']
            position = staff.position or 'Staff Member'
            
            print(f"{staff.full_name:<30} {username:<20} {password:<15} {position:<25}")
        
        print()
    else:
        print("\n💡 No new user accounts were created.")
        print("All staff members already have user accounts.")
    
    # Show all current staff
    print("\n📊 ALL STAFF MEMBERS IN SYSTEM:")
    print("-" * 50)
    all_staff = Staff.objects.all().order_by('full_name')
    
    for staff in all_staff:
        user_info = f"User: {staff.user.username}" if staff.user else "❌ No user account"
        print(f"• {staff.full_name:<30} | {staff.position or 'N/A':<25} | {user_info}")
    
    print(f"\n📈 Statistics:")
    print(f"   Total Staff: {Staff.objects.count()}")
    print(f"   Staff with User Accounts: {Staff.objects.filter(user__isnull=False).count()}")
    print(f"   Total Users: {User.objects.count()}")
    
    print("\n🌐 Access Information:")
    print("   Staff Portal: http://localhost:8000/staff/")
    print("   Django Admin: http://localhost:8000/admin/")
    print("   Login Page: http://localhost:8000/accounts/login/")
    
    print("\n💡 Notes:")
    print("   - All users have staff-level permissions")
    print("   - Default password format: FirstName2024!")
    print("   - Users should change passwords on first login")
    
    # Save credentials to file
    if created_users:
        credentials_file = 'staff_credentials.txt'
        with open(credentials_file, 'w') as f:
            f.write("#FahanieCares Staff User Credentials\n")
            f.write("="*50 + "\n\n")
            
            for user_data in created_users:
                staff = user_data['staff']
                f.write(f"Name: {staff.full_name}\n")
                f.write(f"Position: {staff.position or 'N/A'}\n")
                f.write(f"Division: {staff.get_division_display() or 'N/A'}\n")
                f.write(f"Username: {user_data['username']}\n")
                f.write(f"Password: {user_data['password']}\n")
                f.write(f"Email: {user_data['email']}\n")
                f.write("-" * 40 + "\n")
            
            f.write("\nAccess URLs:\n")
            f.write("Staff Portal: http://localhost:8000/staff/\n")
            f.write("Django Admin: http://localhost:8000/admin/\n")
            f.write("Login Page: http://localhost:8000/accounts/login/\n")
        
        print(f"\n💾 Credentials saved to: {credentials_file}")
    
    print("\n✨ Staff user creation completed!")

if __name__ == "__main__":
    main()