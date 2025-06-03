#!/usr/bin/env python3
"""
Grant highest admin access to Saidamen Mambayao and Farissnoor Edza.
These are the system developers and need full superuser privileges.
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
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.staff.models import Staff

User = get_user_model()

# Developer accounts to promote
DEVELOPERS = [
    {
        'username': 'saidamen.m',
        'full_name': 'Saidamen Mambayao',
        'email': 'bmsaimambayao@gmail.com',
        'role': 'SLSO I / OIC Legislative Affairs / System Developer'
    },
    {
        'username': 'farissnoor.e', 
        'full_name': 'Farissnoor Edza',
        'email': 'farissnooredza99@gmail.com',
        'role': 'IT Staff / Lead Developer'
    }
]

def create_developer_group():
    """Create a System Developers group with all permissions"""
    print("🔧 Creating System Developers group...")
    
    # Create or get the group
    group, created = Group.objects.get_or_create(
        name='System Developers',
        defaults={'name': 'System Developers'}
    )
    
    if created:
        print("✅ Created 'System Developers' group")
    else:
        print("ℹ️  'System Developers' group already exists")
    
    # Get all permissions and add them to the group
    all_permissions = Permission.objects.all()
    group.permissions.set(all_permissions)
    
    print(f"✅ Added {all_permissions.count()} permissions to System Developers group")
    
    return group

def grant_superuser_access():
    """Grant superuser access to developer accounts"""
    print("\n👑 Granting superuser access to developers...")
    print("=" * 60)
    
    # Create developer group first
    dev_group = create_developer_group()
    
    promoted_count = 0
    errors = []
    
    for dev in DEVELOPERS:
        try:
            username = dev['username']
            full_name = dev['full_name']
            email = dev['email']
            role = dev['role']
            
            print(f"\n🔍 Processing: {full_name} ({username})")
            
            # Get or create user
            try:
                user = User.objects.get(username=username)
                print(f"  ✅ Found existing user")
            except User.DoesNotExist:
                print(f"  ⚠️  User not found, creating...")
                # Parse name parts
                name_parts = full_name.split()
                first_name = name_parts[0] if name_parts else full_name
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=f"{first_name}2024!",
                    first_name=first_name,
                    last_name=last_name
                )
                print(f"  ✅ Created user account")
            
            # Grant superuser privileges
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            user.save()
            
            print(f"  👑 Granted SUPERUSER status")
            print(f"  ✅ Granted staff access")
            print(f"  ✅ Account activated")
            
            # Add to developer group
            user.groups.add(dev_group)
            print(f"  👥 Added to System Developers group")
            
            # Grant all individual permissions (belt and suspenders approach)
            all_permissions = Permission.objects.all()
            user.user_permissions.set(all_permissions)
            print(f"  🔐 Granted {all_permissions.count()} individual permissions")
            
            # Update staff profile if exists
            try:
                staff = Staff.objects.get(full_name=full_name)
                original_position = staff.position
                staff.position = role
                staff.user = user
                staff.save()
                print(f"  📝 Updated staff profile position: '{original_position}' → '{role}'")
            except Staff.DoesNotExist:
                print(f"  ⚠️  No staff profile found for {full_name}")
            
            promoted_count += 1
            print(f"  🎉 {full_name} now has FULL ADMIN ACCESS")
            
        except Exception as e:
            error_msg = f"Error processing {dev.get('full_name', 'Unknown')}: {str(e)}"
            errors.append(error_msg)
            print(f"  ❌ {error_msg}")
    
    return promoted_count, errors, dev_group

def verify_admin_access():
    """Verify that developers have proper admin access"""
    print(f"\n🔍 Verifying admin access...")
    print("=" * 60)
    
    for dev in DEVELOPERS:
        username = dev['username']
        full_name = dev['full_name']
        
        try:
            user = User.objects.get(username=username)
            
            print(f"\n👤 {full_name} ({username}):")
            print(f"  🔹 Superuser: {'✅ YES' if user.is_superuser else '❌ NO'}")
            print(f"  🔹 Staff: {'✅ YES' if user.is_staff else '❌ NO'}")
            print(f"  🔹 Active: {'✅ YES' if user.is_active else '❌ NO'}")
            print(f"  🔹 Groups: {', '.join([g.name for g in user.groups.all()]) or 'None'}")
            print(f"  🔹 Individual Permissions: {user.user_permissions.count()}")
            print(f"  🔹 All Permissions (via groups): {user.get_all_permissions().__len__()}")
            
            # Check Django admin access
            can_access_admin = user.is_superuser and user.is_staff and user.is_active
            print(f"  🔹 Django Admin Access: {'✅ YES' if can_access_admin else '❌ NO'}")
            
        except User.DoesNotExist:
            print(f"  ❌ User {username} not found!")

def update_credentials_file():
    """Update credentials file to reflect developer status"""
    print(f"\n📝 Updating credentials file...")
    
    staff_members = Staff.objects.all().select_related('user').order_by('full_name')
    
    content = "#FahanieCares Staff Login Credentials\n"
    content += "=" * 60 + "\n"
    content += "Updated from Staff Profiles.csv (Developers promoted to superusers)\n\n"
    
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
            
            # Mark developers specially
            if username in ['saidamen.m', 'farissnoor.e']:
                admin_status = " [SUPERUSER/DEVELOPER]"
            else:
                admin_status = ""
                
        else:
            username = "No account"
            password = "No account"
            email = staff.email or "No email"
            admin_status = ""
        
        content += f"Name: {name}{admin_status}\n"
        content += f"Position: {position}\n"
        content += f"Division: {division_display}\n"
        content += f"Employment Status: {staff.get_employment_status_display() or 'Unknown'}\n"
        content += f"Office: {staff.get_office_display() or 'Unknown'}\n"
        content += f"Phone: {staff.phone_number or 'Not provided'}\n"
        content += f"Username: {username}\n"
        content += f"Password: {password}\n"
        content += f"Email: {email}\n"
        
        if username in ['saidamen.m', 'farissnoor.e']:
            content += f"Access Level: SUPERUSER - Full Django Admin & System Access\n"
        
        content += "-" * 40 + "\n"
    
    content += "\nAccess URLs:\n"
    content += "Staff Portal: http://localhost:8000/staff/\n"
    content += "Django Admin: http://localhost:8000/admin/ (Superusers have full access)\n"
    content += "Login Page: http://localhost:8000/accounts/login/\n\n"
    content += "Notes:\n"
    content += "- Saidamen Mambayao & Farissnoor Edza: SUPERUSERS/DEVELOPERS\n"
    content += "- Superusers have full Django admin panel access\n"
    content += "- Superusers can manage all users, permissions, and system settings\n"
    content += "- New users should change their password on first login\n"
    content += "- Contact developers for system administration needs\n"
    
    with open('staff_login_credentials.txt', 'w') as f:
        f.write(content)
    
    print(f"✅ Updated staff_login_credentials.txt with developer privileges noted")

if __name__ == '__main__':
    print("👑 GRANTING DEVELOPER ADMIN ACCESS")
    print("=" * 60)
    print("Promoting Saidamen Mambayao & Farissnoor Edza to SUPERUSERS")
    print("They are the system developers and need full admin access")
    print("=" * 60)
    
    # Grant superuser access
    promoted, errors, dev_group = grant_superuser_access()
    
    # Verify access
    verify_admin_access()
    
    # Update credentials file
    update_credentials_file()
    
    print(f"\n🎉 DEVELOPER PROMOTION COMPLETED!")
    print(f"👑 {promoted} developers promoted to SUPERUSER status")
    print(f"👥 Added to '{dev_group.name}' group")
    print(f"🔐 Full Django admin panel access granted")
    print(f"📝 Credentials file updated with admin privileges")
    
    if errors:
        print(f"\n❌ Errors encountered:")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"\n✅ No errors - all developers successfully promoted!")