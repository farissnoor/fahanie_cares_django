#!/usr/bin/env python
"""
Script to create user accounts for staff members synced from Notion.
This will sync staff data from Notion and create Django user accounts with default credentials.
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
from django.utils.text import slugify
from apps.staff.models import Staff
from utils.notion.staff import StaffNotionService
import re

User = get_user_model()

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
    # Capitalize first letter
    password = first_name.capitalize() + "2024!"
    return password

def sync_staff_and_create_users():
    """Sync staff from Notion and create user accounts."""
    print("🔄 Starting staff sync from Notion...")
    
    try:
        # Initialize Notion service
        notion_service = StaffNotionService()
        
        # Sync staff from Notion
        synced_staff = notion_service.sync_staff_from_notion()
        
        print(f"✅ Successfully synced {len(synced_staff)} staff members from Notion")
        
        # Create user accounts for staff
        created_users = []
        updated_users = []
        
        for staff_data in synced_staff:
            staff = staff_data['staff']
            
            # Skip if staff already has a user account
            if staff.user:
                print(f"⏭️  {staff.full_name} already has a user account: {staff.user.username}")
                continue
            
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
            
            created_users.append({
                'staff': staff,
                'username': username,
                'password': password,
                'email': user.email
            })
            
            print(f"✅ Created user account for {staff.full_name}: {username}")
        
        return synced_staff, created_users
        
    except Exception as e:
        print(f"❌ Error syncing staff: {str(e)}")
        return [], []

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
    print(f"{'FULL NAME':<25} {'USERNAME':<20} {'PASSWORD':<15} {'EMAIL':<30}")
    print("-" * 90)
    
    # User rows
    for user_data in created_users:
        staff = user_data['staff']
        username = user_data['username']
        password = user_data['password']
        email = user_data['email']
        
        print(f"{staff.full_name:<25} {username:<20} {password:<15} {email:<30}")
    
    print()
    print("💡 Notes:")
    print("- All users have staff permissions (can access Django admin)")
    print("- Default password format: FirstName2024!")
    print("- Users should change their passwords on first login")
    print("- Email format: username@fahanie.gov.ph (if no email provided)")
    print()
    print("🌐 Access URLs:")
    print("- Staff Portal: http://localhost:8000/staff/")
    print("- Django Admin: http://localhost:8000/admin/")
    print("- Login Page: http://localhost:8000/accounts/login/")

def main():
    """Main execution function."""
    print("🚀 Creating staff user accounts...")
    print()
    
    # Sync staff and create users
    synced_staff, created_users = sync_staff_and_create_users()
    
    # Print summary
    print_credentials_summary(created_users)
    
    # Save credentials to file
    if created_users:
        credentials_file = 'staff_credentials.txt'
        with open(credentials_file, 'w') as f:
            f.write("STAFF USER CREDENTIALS\n")
            f.write("="*50 + "\n\n")
            f.write(f"Created: {len(created_users)} accounts\n\n")
            
            for user_data in created_users:
                staff = user_data['staff']
                f.write(f"Name: {staff.full_name}\n")
                f.write(f"Username: {user_data['username']}\n")
                f.write(f"Password: {user_data['password']}\n")
                f.write(f"Email: {user_data['email']}\n")
                f.write(f"Position: {staff.position}\n")
                f.write(f"Division: {staff.get_division_display()}\n")
                f.write("-" * 30 + "\n")
            
            f.write("\nAccess URLs:\n")
            f.write("- Staff Portal: http://localhost:8000/staff/\n")
            f.write("- Django Admin: http://localhost:8000/admin/\n")
            f.write("- Login Page: http://localhost:8000/accounts/login/\n")
        
        print(f"💾 Credentials saved to: {credentials_file}")
    
    print("\n✨ Staff user creation completed!")

if __name__ == "__main__":
    main()