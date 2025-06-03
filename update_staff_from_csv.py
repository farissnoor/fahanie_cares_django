#!/usr/bin/env python3
"""
Update staff profiles in Django system based on Staff Profiles.csv data.
"""

import os
import sys
import django
import csv
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

# Division mapping from CSV to model choices
DIVISION_MAPPING = {
    'Legislative Affairs': 'legislative_affairs',
    'Administrative Affairs': 'administrative_affairs', 
    'Communications': 'communications',
    'IT Unit': 'it_unit',
    'MP Office': 'mp_office'
}

# Employment status mapping
EMPLOYMENT_MAPPING = {
    'Contractual': 'contractual',
    'Coterminous': 'coterminous',
    'Consultant': 'consultant',
    'Intern': 'intern',
    'Volunteer': 'volunteer'
}

# Office mapping
OFFICE_MAPPING = {
    'Main Office': 'main_office',
    'Satellite Office': 'satellite_office'
}

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

def create_or_update_staff_from_csv():
    """Read CSV and create/update staff profiles"""
    csv_file_path = '/Users/macbookpro/Documents/fahanie-cares/docs/Staff Profiles.csv'
    
    updated_count = 0
    created_count = 0
    errors = []
    
    with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            try:
                full_name = row['Full Name'].strip()
                if not full_name:
                    continue
                
                position = row['Position/Designation'].strip()
                division_text = row['Division'].strip()
                employment_status_text = row['Employment Status'].strip()
                phone_number = row['Phone Number'].strip()
                email = row['Email Address'].strip()
                address = row['Address'].strip()
                supervisor_name = row['Supervisor'].strip()
                duties = row['Duties and Responsibilities'].strip()
                office_text = row['Office'].strip()
                workflow = row['Staff Workflow'].strip()
                
                # Map values to model choices
                division = DIVISION_MAPPING.get(division_text, 'administrative_affairs')
                employment_status = EMPLOYMENT_MAPPING.get(employment_status_text, 'contractual')
                office = OFFICE_MAPPING.get(office_text, 'main_office')
                
                # Generate username and check if user exists
                username = generate_username(full_name)
                password = generate_password(full_name)
                
                # Parse name parts
                name_parts = full_name.split()
                first_name = name_parts[0] if name_parts else full_name
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                
                # Try to find existing user
                user = None
                try:
                    user = User.objects.get(username=username)
                    print(f"Found existing user: {username}")
                except User.DoesNotExist:
                    # Create new user if email is provided
                    if email:
                        try:
                            user = User.objects.create_user(
                                username=username,
                                email=email,
                                password=password,
                                first_name=first_name,
                                last_name=last_name,
                                is_staff=True,
                                is_active=True
                            )
                            print(f"Created new user: {username}")
                        except Exception as e:
                            print(f"Error creating user {username}: {e}")
                            continue
                
                # Create or update staff profile
                staff, created = Staff.objects.get_or_create(
                    full_name=full_name,
                    defaults={
                        'user': user,
                        'notion_id': str(uuid.uuid4()),
                        'position': position,
                        'division': division,
                        'employment_status': employment_status,
                        'phone_number': phone_number,
                        'email': email or (user.email if user else ''),
                        'address': address,
                        'duties_responsibilities': duties,
                        'staff_workflow': workflow,
                        'office': office,
                        'is_active': True,
                        'date_hired': datetime.now().date()
                    }
                )
                
                if created:
                    created_count += 1
                    print(f"✅ Created staff profile: {full_name}")
                else:
                    # Update existing staff profile
                    staff.user = user
                    staff.position = position
                    staff.division = division
                    staff.employment_status = employment_status
                    staff.phone_number = phone_number
                    if email:
                        staff.email = email
                    staff.address = address
                    staff.duties_responsibilities = duties
                    staff.staff_workflow = workflow
                    staff.office = office
                    staff.save()
                    
                    updated_count += 1
                    print(f"✅ Updated staff profile: {full_name}")
                
                # Print summary of staff data
                print(f"   Position: {position}")
                print(f"   Division: {division_text} -> {division}")
                print(f"   Employment: {employment_status_text} -> {employment_status}")
                print(f"   Office: {office_text} -> {office}")
                print(f"   Phone: {phone_number}")
                print(f"   Email: {email}")
                print(f"   Username: {username}")
                print("-" * 50)
                
            except Exception as e:
                error_msg = f"Error processing {row.get('Full Name', 'Unknown')}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
    
    print(f"\n📊 Summary:")
    print(f"✅ Created: {created_count} staff profiles")
    print(f"🔄 Updated: {updated_count} staff profiles")
    print(f"❌ Errors: {len(errors)}")
    
    if errors:
        print("\nErrors encountered:")
        for error in errors:
            print(f"  - {error}")
    
    return created_count, updated_count, errors

def update_credentials_file():
    """Update staff_login_credentials.txt with all current staff"""
    staff_members = Staff.objects.all().select_related('user').order_by('full_name')
    
    content = "#FahanieCares Staff Login Credentials\n"
    content += "=" * 60 + "\n"
    content += "Updated from Staff Profiles.csv\n\n"
    
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
    content += "- New users should change their password on first login\n"
    content += "- All staff have Django admin access\n"
    content += "- Contact IT for password resets\n"
    
    with open('staff_login_credentials.txt', 'w') as f:
        f.write(content)
    
    print(f"✅ Updated staff_login_credentials.txt with {staff_members.count()} staff members")

if __name__ == '__main__':
    print("Updating staff profiles from CSV...")
    print("=" * 60)
    
    created, updated, errors = create_or_update_staff_from_csv()
    
    print("\nUpdating credentials file...")
    update_credentials_file()
    
    print(f"\n🎉 Process completed!")
    print(f"📝 Check staff_login_credentials.txt for updated credentials")