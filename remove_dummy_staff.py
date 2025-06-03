#!/usr/bin/env python3
"""
Remove dummy staff members (Jane Smith, John Doe, Maria Santos) from the entire system.
These were test/development users not in the actual Staff Profiles.csv.
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

# Dummy staff to remove (these were NOT in the CSV file)
DUMMY_STAFF = [
    {
        'username': 'jane.s',
        'full_name': 'Jane B. Smith',
        'email': 'jane.smith@fahanie.gov.ph'
    },
    {
        'username': 'john.d', 
        'full_name': 'John A. Doe',
        'email': 'john.doe@fahanie.gov.ph'
    },
    {
        'username': 'maria.s',
        'full_name': 'Maria C. Santos', 
        'email': 'maria.santos@fahanie.gov.ph'
    }
]

def remove_dummy_staff():
    """Remove dummy staff users and profiles completely"""
    
    print("🗑️  Removing dummy staff from the system...")
    print("=" * 60)
    
    removed_users = 0
    removed_staff = 0
    errors = []
    
    for dummy in DUMMY_STAFF:
        username = dummy['username']
        full_name = dummy['full_name']
        
        try:
            print(f"\n🔍 Processing: {full_name} ({username})")
            
            # Remove Staff profile first
            try:
                staff_profiles = Staff.objects.filter(full_name=full_name)
                if staff_profiles.exists():
                    staff_count = staff_profiles.count()
                    staff_profiles.delete()
                    removed_staff += staff_count
                    print(f"  ✅ Removed {staff_count} staff profile(s)")
                else:
                    print(f"  ℹ️  No staff profile found")
            except Exception as e:
                print(f"  ❌ Error removing staff profile: {e}")
                errors.append(f"Staff profile error for {full_name}: {e}")
            
            # Remove User account
            try:
                user = User.objects.get(username=username)
                user_email = user.email
                user.delete()
                removed_users += 1
                print(f"  ✅ Removed user account: {username} ({user_email})")
            except User.DoesNotExist:
                print(f"  ℹ️  User {username} not found")
            except Exception as e:
                print(f"  ❌ Error removing user: {e}")
                errors.append(f"User removal error for {username}: {e}")
                
        except Exception as e:
            error_msg = f"General error processing {full_name}: {e}"
            errors.append(error_msg)
            print(f"  ❌ {error_msg}")
    
    print(f"\n📊 Removal Summary:")
    print(f"✅ Removed {removed_users} user accounts")
    print(f"✅ Removed {removed_staff} staff profiles") 
    print(f"❌ Errors: {len(errors)}")
    
    if errors:
        print("\n❌ Errors encountered:")
        for error in errors:
            print(f"  - {error}")
    
    return removed_users, removed_staff, errors

def verify_remaining_staff():
    """Verify the remaining staff are legitimate"""
    print(f"\n🔍 Verifying remaining staff...")
    
    remaining_staff = Staff.objects.all().order_by('full_name')
    print(f"📋 Remaining staff count: {remaining_staff.count()}")
    
    print("\n📋 Remaining staff members:")
    for staff in remaining_staff:
        status = "✅ Real" if staff.user else "⚠️  No User Account"
        print(f"  - {staff.full_name} ({staff.position or 'Staff'}) [{status}]")
    
    return remaining_staff.count()

def update_credentials_file():
    """Update staff_login_credentials.txt without dummy staff"""
    staff_members = Staff.objects.all().select_related('user').order_by('full_name')
    
    content = "#FahanieCares Staff Login Credentials\n"
    content += "=" * 60 + "\n"
    content += "Updated from Staff Profiles.csv (Dummy staff removed)\n\n"
    
    def generate_password(name):
        first_name = name.strip().split()[0]
        return f"{first_name}2024!"
    
    for staff in staff_members:
        name = staff.full_name
        position = staff.position or "Staff"
        
        # Map division back to display name
        division_display = {
            'legislative_affairs': 'Legislative Affairs',
            'administrative_affairs': 'Administrative Affairs',
            'communications': 'Communications',
            'it_unit': 'IT Unit',
            'mp_office': "MP Uy-Oyod's Office"
        }.get(staff.division, staff.division or "Administrative Affairs")
        
        if staff.user:
            username = staff.user.username
            password = generate_password(name)
            email = staff.email or staff.user.email
        else:
            username = "No account"
            password = "No account"
            email = staff.email or "No email"
        
        content += f"Name: {name}\n"
        content += f"Position: {position}\n"
        content += f"Division: {division_display}\n"
        content += f"Employment Status: {staff.get_employment_status_display() or 'Unknown'}\n"
        content += f"Office: {staff.get_office_display() or 'Unknown'}\n"
        content += f"Phone: {staff.phone_number or 'Not provided'}\n"
        content += f"Username: {username}\n"
        content += f"Password: {password}\n"
        content += f"Email: {email}\n"
        content += "-" * 40 + "\n"
    
    content += "\nAccess URLs:\n"
    content += "Staff Portal: http://localhost:8000/staff/\n"
    content += "Django Admin: http://localhost:8000/admin/\n"
    content += "Login Page: http://localhost:8000/accounts/login/\n\n"
    content += "Notes:\n"
    content += "- Profiles updated from Staff Profiles.csv\n"
    content += "- Dummy staff (Jane Smith, John Doe, Maria Santos) removed\n"
    content += "- New users should change their password on first login\n"
    content += "- All staff have Django admin access\n"
    content += "- Contact IT for password resets\n"
    
    with open('staff_login_credentials.txt', 'w') as f:
        f.write(content)
    
    print(f"✅ Updated staff_login_credentials.txt with {staff_members.count()} legitimate staff members")

if __name__ == '__main__':
    print("🧹 CLEANING UP DUMMY STAFF DATA")
    print("=" * 60)
    print("Removing Jane B. Smith, John A. Doe, and Maria C. Santos")
    print("(These were dummy/test users not in Staff Profiles.csv)")
    print("=" * 60)
    
    # Remove dummy staff
    removed_users, removed_staff, errors = remove_dummy_staff()
    
    # Verify remaining staff
    remaining_count = verify_remaining_staff()
    
    # Update credentials file
    print(f"\n📝 Updating credentials file...")
    update_credentials_file()
    
    print(f"\n🎉 CLEANUP COMPLETED!")
    print(f"✅ Removed {removed_users} dummy user accounts")
    print(f"✅ Removed {removed_staff} dummy staff profiles")
    print(f"✅ {remaining_count} legitimate staff members remain")
    print(f"📝 Credentials file updated without dummy data")