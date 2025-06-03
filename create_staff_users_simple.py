#!/usr/bin/env python
"""
Simple script to create staff members and their user accounts directly from Notion data.
This bypasses the complex Notion service to avoid recursion issues.
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

User = get_user_model()

# Sample staff data based on what we saw from Notion
STAFF_DATA = [
    {
        'full_name': 'Rohamiah E. Ibrahim',
        'position': 'Coordinator',
        'email': 'rohamiah.ibrahim@fahanie.gov.ph',
        'phone_number': '09505725102',
        'address': 'RH IV, Cotabato City',
        'division': 'administrative_affairs',
        'employment_status': 'contractual',
        'office': 'main_office',
    },
    {
        'full_name': 'Mae Anne C. Lidasan',
        'position': 'Coordinator',
        'email': 'maeanne.lidasan@fahanie.gov.ph',
        'phone_number': '09366186579',
        'address': 'RH IV, Cotabato City',
        'division': 'administrative_affairs',
        'employment_status': 'contractual',
        'office': 'main_office',
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
        'duties_responsibilities': 'Member of Parliament representing RH IV, Cotabato City',
        'staff_workflow': 'Parliamentary sessions, constituent services, policy development'
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

def create_staff_and_users():
    """Create staff members and their user accounts."""
    print("🚀 Creating staff members and user accounts...")
    print()
    
    created_users = []
    
    for staff_data in STAFF_DATA:
        full_name = staff_data['full_name']
        
        # Check if staff already exists
        existing_staff = Staff.objects.filter(full_name=full_name).first()
        if existing_staff:
            print(f"⏭️  Staff member {full_name} already exists")
            if existing_staff.user:
                print(f"   └── Already has user account: {existing_staff.user.username}")
                continue
            else:
                staff = existing_staff
                print(f"   └── Creating user account for existing staff...")
        else:
            # Create new staff member
            staff = Staff.objects.create(**staff_data)
            print(f"✅ Created staff member: {full_name}")
        
        # Generate username and password
        username = create_username(full_name)
        password = create_default_password(full_name)
        
        # Extract name parts for user creation
        name_parts = full_name.strip().split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        # Create user account
        user = User.objects.create_user(
            username=username,
            email=staff_data.get('email', f"{username}@fahanie.gov.ph"),
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,  # Give staff permissions
            is_active=True
        )
        
        # Link user to staff profile
        staff.user = user
        staff.save()
        
        created_users.append({
            'staff': staff,
            'username': username,
            'password': password,
            'email': user.email
        })
        
        print(f"✅ Created user account: {username}")
    
    return created_users

def print_credentials_summary(created_users):
    """Print a summary of created user credentials."""
    print("\n" + "="*80)
    print("📋 STAFF USER CREDENTIALS SUMMARY")
    print("="*80)
    print()
    
    if not created_users:
        print("No new user accounts were created.")
        print("All staff members may already have user accounts.")
        return
    
    print(f"Created {len(created_users)} new user accounts:")
    print()
    
    # Table header
    print(f"{'FULL NAME':<25} {'USERNAME':<20} {'PASSWORD':<15} {'EMAIL':<35}")
    print("-" * 95)
    
    # User rows
    for user_data in created_users:
        staff = user_data['staff']
        username = user_data['username']
        password = user_data['password']
        email = user_data['email']
        
        print(f"{staff.full_name:<25} {username:<20} {password:<15} {email:<35}")
    
    print()
    print("💡 Notes:")
    print("- All users have staff permissions (can access Django admin)")
    print("- Default password format: FirstName2024!")
    print("- Users should change their passwords on first login")
    print("- Access the staff portal at: http://localhost:8000/staff/")
    print()
    print("🌐 Quick Access URLs:")
    print("- Staff Portal: http://localhost:8000/staff/")
    print("- Django Admin: http://localhost:8000/admin/")
    print("- Login Page: http://localhost:8000/accounts/login/")

def save_credentials_to_file(created_users):
    """Save credentials to a file for reference."""
    if not created_users:
        return
    
    credentials_file = 'staff_credentials.txt'
    with open(credentials_file, 'w') as f:
        f.write("#FahanieCares Staff User Credentials\n")
        f.write("="*50 + "\n\n")
        f.write(f"Generated: {len(created_users)} accounts\n")
        f.write("Date: " + str(django.utils.timezone.now().date()) + "\n\n")
        
        for user_data in created_users:
            staff = user_data['staff']
            f.write(f"Staff Member: {staff.full_name}\n")
            f.write(f"Position: {staff.position or 'N/A'}\n")
            f.write(f"Division: {staff.get_division_display() or 'N/A'}\n")
            f.write(f"Username: {user_data['username']}\n")
            f.write(f"Password: {user_data['password']}\n")
            f.write(f"Email: {user_data['email']}\n")
            f.write("-" * 40 + "\n")
        
        f.write("\nAccess Information:\n")
        f.write("Staff Portal: http://localhost:8000/staff/\n")
        f.write("Django Admin: http://localhost:8000/admin/\n")
        f.write("Login Page: http://localhost:8000/accounts/login/\n\n")
        f.write("Notes:\n")
        f.write("- All accounts have staff-level permissions\n")
        f.write("- Password format: FirstName2024!\n")
        f.write("- Users should change passwords on first login\n")
    
    print(f"💾 Credentials saved to: {credentials_file}")

def main():
    """Main execution function."""
    print("🚀 Staff User Account Creation")
    print("Creating staff members and user accounts...")
    print()
    
    # Create staff and users
    created_users = create_staff_and_users()
    
    # Print summary
    print_credentials_summary(created_users)
    
    # Save to file
    save_credentials_to_file(created_users)
    
    print("\n✨ Staff user creation completed!")
    print("🔗 You can now access the staff portal at: http://localhost:8000/staff/")

if __name__ == "__main__":
    main()