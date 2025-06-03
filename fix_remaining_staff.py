#!/usr/bin/env python3
"""
Fix the 2 staff members that failed due to phone number field length.
"""

import os
import sys
import django
import uuid

# Add the project root to Python path
sys.path.append('/Users/macbookpro/Documents/fahanie-cares/fahanie_cares_django')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.staff.models import Staff
from datetime import datetime

User = get_user_model()

def create_remaining_staff():
    """Create the 2 staff members that failed"""
    
    # Schejah E. Sindatok
    staff_data_1 = {
        'full_name': 'Schejah E. Sindatok',
        'position': 'PAO IV',
        'division': 'administrative_affairs',
        'employment_status': 'coterminous',
        'phone_number': '09455349686/ 09684168139',  # This was causing the error
        'email': 'schejah@gmail.com',
        'address': 'Cotabato City',
        'duties_responsibilities': """A. Travel/flight bookings, hotel accommodations, visa compliance and other related matters for MP and staff.
B. Secure copy of TA and TO, through Hasnah.
C. Secure Order of Business in relation to BTA matters. 
D. Continue with the calendar regarding committee sessions. OB's should be forwarded to Kate/Hasnah.
E. Update schedule of MP both BTA matters and social engagements if the invitations were coursed through the office. Both from office email and MP's BTA email.
F. Take down notes during office meetings and other relevant matters and prepare the TSN (transcript of notes). Use the AI app. 
G. Assess Solicitations. Make a database (date/who requested/what is requested -amount/remarks-declined/approved or for reconsideration).
H. Receiving emails and other communications including phones.
I.  Contacts and follow up concerned persons
J. Secure Petty Cash of the office and manage day to day expenses. 
K. Answers inquiries from the FB page and sms from the office phone
L. Update the calendar in the NOTION app.
M. Do the grocery shopping for monthly office snacks and cleaning supplies for both main and satellite offices.
N. Authorized to encash office cheques with Nas and Allysa.
O. Transacts other personal matters for MP.""",
        'office': 'main_office',
        'username': 'schejah.s'
    }
    
    # Mokadafy I. Ebus  
    staff_data_2 = {
        'full_name': 'Mokadafy I. Ebus',
        'position': 'Staff',
        'division': 'administrative_affairs',
        'employment_status': 'contractual',
        'phone_number': '09260962733/09464109886',  # This was causing the error
        'email': '',
        'address': 'Datu Piang, Maguindanao del Sur',
        'duties_responsibilities': '',
        'office': 'satellite_office',
        'username': 'mokadafy.e'
    }
    
    for staff_data in [staff_data_1, staff_data_2]:
        try:
            # Get existing user
            user = User.objects.get(username=staff_data['username'])
            
            # Create staff profile
            staff, created = Staff.objects.get_or_create(
                full_name=staff_data['full_name'],
                defaults={
                    'user': user,
                    'notion_id': str(uuid.uuid4()),
                    'position': staff_data['position'],
                    'division': staff_data['division'],
                    'employment_status': staff_data['employment_status'],
                    'phone_number': staff_data['phone_number'],
                    'email': staff_data['email'],
                    'address': staff_data['address'],
                    'duties_responsibilities': staff_data['duties_responsibilities'],
                    'office': staff_data['office'],
                    'is_active': True,
                    'date_hired': datetime.now().date()
                }
            )
            
            if created:
                print(f"✅ Created staff profile: {staff_data['full_name']}")
            else:
                print(f"✅ Staff profile already exists: {staff_data['full_name']}")
                
        except Exception as e:
            print(f"❌ Error creating {staff_data['full_name']}: {e}")

if __name__ == '__main__':
    print("Creating remaining staff profiles...")
    create_remaining_staff()
    print("Done!")