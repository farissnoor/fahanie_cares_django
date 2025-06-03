"""
Script to create test data for #FahanieCares system.
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.constituents.models import Constituent
from apps.referrals.models import ServiceCategory, Service, Referral
from apps.chapters.models import Chapter, ChapterMembership
from apps.services.models import ServiceProgram, ServiceApplication

User = get_user_model()

def create_users():
    """Create test users of different types."""
    print("Creating users...")
    
    # MP user
    mp_user = User.objects.create_user(
        username='mp_fahanie',
        email='mp@fahaniecares.ph',
        password='Test@Pass123!',
        first_name='Sittie Fahanie',
        last_name='Uy-Oyod',
        user_type='mp',
        is_approved=True,
        municipality='Datu Piang',
        province='Maguindanao del Sur',
        address='District Office, Datu Piang, Maguindanao del Sur',
        phone='+63 XXX XXX XXXX'
    )
    
    # Staff users
    staff_users = []
    for i in range(3):
        staff_user = User.objects.create_user(
            username=f'staff{i+1}',
            email=f'staff{i+1}@fahaniecares.ph',
            password='Test@Pass123!',
            first_name=f'Staff',
            last_name=f'Member {i+1}',
            user_type='staff',
            is_approved=True
        )
        staff_users.append(staff_user)
    
    # Chapter coordinators
    coordinators = []
    municipalities = ['Datu Piang', 'Datu Saudi-Ampatuan', 'Datu Salibo', 'Shariff Saydona Mustapha', 
                      'Mamasapano', 'Shariff Aguak', 'Datu Unsay']
    for i, municipality in enumerate(municipalities):
        username = municipality.lower().replace(' ', '_').replace('-', '_')
        email = municipality.lower().replace(' ', '').replace('-', '')
        
        coordinator = User.objects.create_user(
            username=f'coord_{username}',
            email=f'coordinator.{email}@fahaniecares.ph',
            password='Test@Pass123!',
            first_name=f'Coordinator',
            last_name=municipality,
            user_type='coordinator',
            municipality=municipality,
            province='Maguindanao del Sur',
            is_approved=True
        )
        coordinators.append(coordinator)
    
    # Regular members
    members = []
    for i in range(20):
        member = User.objects.create_user(
            username=f'member{i+1}',
            email=f'member{i+1}@example.com',
            password='Test@Pass123!',
            first_name=f'Member',
            last_name=f'Number {i+1}',
            user_type='member',
            is_approved=True
        )
        members.append(member)
    
    # Constituents
    constituents = []
    municipalities = ['Datu Piang', 'Datu Saudi-Ampatuan', 'Datu Salibo', 'Shariff Saydona Mustapha', 
                     'Mamasapano', 'Shariff Aguak', 'Datu Unsay']
    
    # Define common Muslim/Maguindanaon names
    first_names = [
        'Abdul', 'Mohammed', 'Ali', 'Hassan', 'Ibrahim', 'Omar', 'Malik', 'Yusuf', 'Rashid', 'Jamal',
        'Fatima', 'Aisha', 'Zainab', 'Mariam', 'Amina', 'Khadija', 'Layla', 'Noor', 'Siti', 'Zahra'
    ]
    
    last_names = [
        'Adiong', 'Alonto', 'Balindong', 'Dimaporo', 'Gandamra', 'Hassan', 'Macarambon', 'Macapagal',
        'Mangudadatu', 'Mastura', 'Matalam', 'Paglas', 'Sinsuat', 'Sema', 'Tomawis', 'Uy', 'Zubiri'
    ]
    
    # Define barangays by municipality
    barangays = {
        'Datu Piang': ['Balong', 'Buayan', 'Damabalas', 'Damalusay', 'Dulawan', 
                      'Kanguan', 'Kalipapa', 'Liong', 'Magaslong', 'Montay', 'Poblacion'],
        'Datu Saudi-Ampatuan': ['Dapiawan', 'Elian', 'Gawang', 'Kabengi', 'Kitango', 
                               'Kitapok', 'Madia', 'Pagatin', 'Poblacion', 'Salbu'],
        'Datu Salibo': ['Andavit', 'Butilen', 'Pagatin I', 'Pagatin II', 'Pagatin III', 
                       'Pandi', 'Sambulawan', 'Saniag'],
        'Shariff Saydona Mustapha': ['Bakat', 'Nabundas', 'Linantangan', 'Pagatin IV', 'Pamalian',
                                    'Dapiawan', 'Ganta', 'Libutan', 'Tina', 'Poblacion'],
        'Mamasapano': ['Bagumbong', 'Dabenayan', 'Daladap', 'Dasikil', 'Liab', 
                      'Lusay', 'Mamasapano', 'Manongkaling', 'Pimbalakan', 'Sapakan', 'Tuka'],
        'Shariff Aguak': ['Bialong', 'Lapok', 'Lepok', 'Malingao', 'Poblacion', 
                         'Poblacion III', 'Tapikan', 'Taib'],
        'Datu Unsay': ['Maitumaig', 'Meta', 'Pamalian', 'Poblacion', 'Tuntungan']
    }
    
    for i in range(50):
        gender = random.choice(['M', 'F'])
        if gender == 'M':
            first_name = random.choice(first_names[:10])  # Male names
        else:
            first_name = random.choice(first_names[10:])  # Female names
            
        last_name = random.choice(last_names)
        
        municipality = random.choice(municipalities)
        barangay = random.choice(barangays[municipality])
            
        constituent = User.objects.create_user(
            username=f'constituent{i+1}',
            email=f'constituent{i+1}@example.com',
            password='Test@Pass123!',
            first_name=first_name,
            last_name=last_name,
            user_type='constituent',
            province='Maguindanao del Sur',
            municipality=municipality
        )
        
        # Create constituent profile
        Constituent.objects.create(
            user=constituent,
            full_name=f'{constituent.first_name} {constituent.last_name}',
            contact_number=f'09{random.randint(100000000, 999999999)}',
            municipality=municipality,
            province='Maguindanao del Sur',
            barangay=barangay,
            complete_address=f'Purok {random.randint(1, 5)}, {barangay}, {municipality}',
            birth_date=datetime.now().date() - timedelta(days=random.randint(7300, 21900))
        )
        constituents.append(constituent)
    
    print(f"Created {User.objects.count()} users")
    return {
        'mp': mp_user,
        'staff': staff_users,
        'coordinators': coordinators,
        'members': members,
        'constituents': constituents
    }

def create_chapters(users):
    """Create test chapters."""
    print("Creating chapters...")
    
    chapters = []
    municipalities = ['Datu Piang', 'Datu Saudi-Ampatuan', 'Datu Salibo', 'Shariff Saydona Mustapha', 
                      'Mamasapano', 'Shariff Aguak', 'Datu Unsay']
    
    # Create provincial chapter first
    provincial_chapter = Chapter.objects.create(
        name="Maguindanao del Sur Provincial Chapter",
        tier='provincial',
        municipality='Buluan',  # Provincial capital
        province='Maguindanao del Sur',
        country='Philippines',
        description="The provincial chapter of #FahanieCares in Maguindanao del Sur, focusing on serving communities across the province.",
        mission_statement="To bring quality public service and community support to all municipalities of Maguindanao del Sur.",
        established_date=datetime.now().date() - timedelta(days=random.randint(90, 365)),
        status='active',
        coordinator=users['mp'],  # MP as provincial coordinator
        email="maguindanaodelsur@fahaniecares.ph",
        phone=f'09{random.randint(100000000, 999999999)}',
        address='Provincial Capitol, Buluan, Maguindanao del Sur',
        meeting_location='Provincial Capitol Conference Hall',
        meeting_schedule='Every last Friday of the month, 2:00 PM'
    )
    chapters.append(provincial_chapter)
    
    # Create municipal chapters
    for i, municipality in enumerate(municipalities):
        if i < len(users['coordinators']):
            coordinator = users['coordinators'][i]
        else:
            coordinator = random.choice(users['coordinators'])
        
        email = municipality.lower().replace(' ', '').replace('-', '')
        
        chapter = Chapter.objects.create(
            name=f'{municipality} Municipal Chapter',
            tier='municipal',
            municipality=municipality,
            province='Maguindanao del Sur',
            country='Philippines',
            parent_chapter=provincial_chapter,
            description=f'The {municipality} Chapter serves the community of {municipality}, Maguindanao del Sur with various programs.',
            mission_statement=f'To serve the people of {municipality} with compassion and dedication.',
            established_date=datetime.now().date() - timedelta(days=random.randint(90, 365)),
            status='active',
            coordinator=coordinator,
            email=f'{email}@fahaniecares.ph',
            phone=f'09{random.randint(100000000, 999999999)}',
            address=f'{municipality} Municipal Hall',
            meeting_location=f'{municipality} Municipal Gymnasium',
            meeting_schedule='Every 1st Saturday of the month, 2:00 PM'
        )
        chapters.append(chapter)
        
        # Add members to chapters
        chapter_members = random.sample(users['members'], random.randint(5, 10))
        for member in chapter_members:
            ChapterMembership.objects.create(
                chapter=chapter,
                user=member,
                role='member',
                status='active',
                is_volunteer=random.choice([True, False]),
                volunteer_hours=random.randint(0, 100) if random.choice([True, False]) else 0
            )
    
    print(f"Created {Chapter.objects.count()} chapters")
    return chapters

def create_services():
    """Create test services."""
    print("Creating services...")
    
    # Create service categories
    categories = [
        ('Healthcare', 'Medical and health-related services'),
        ('Education', 'Educational assistance and scholarships'),
        ('Legal', 'Legal aid and consultation'),
        ('Livelihood', 'Business and employment assistance'),
        ('Emergency', 'Emergency and disaster relief'),
    ]
    
    service_categories = []
    for name, description in categories:
        category = ServiceCategory.objects.create(
            name=name,
            description=description
        )
        service_categories.append(category)
    
    # Create services
    services = []
    service_list = [
        ('Medical Assistance', 'Healthcare', 'Financial assistance for medical expenses'),
        ('Legal Consultation', 'Legal', 'Free legal advice and representation'),
        ('Educational Scholarship', 'Education', 'Scholarship programs for students'),
        ('Livelihood Training', 'Livelihood', 'Skills training and business support'),
        ('Emergency Relief', 'Emergency', 'Immediate assistance during calamities'),
        ('Medicine Assistance', 'Healthcare', 'Free medicines for constituents'),
        ('Job Placement', 'Livelihood', 'Employment assistance and job matching'),
    ]
    
    for name, category_name, description in service_list:
        category = ServiceCategory.objects.get(name=category_name)
        service = Service.objects.create(
            name=name,
            description=description,
            category=category,
            is_active=True,
            is_featured=random.choice([True, False])
        )
        services.append(service)
    
    print(f"Created {Service.objects.count()} services")
    return services

def create_service_programs():
    """Create test service programs."""
    print("Creating service programs...")
    
    programs = []
    program_list = [
        ('Kalusugan Para Sa Lahat', 'health', 'Comprehensive healthcare program for indigent families'),
        ('Kabataan Iskolar Program', 'educational', 'Scholarship program for deserving students'),
        ('Hanapbuhay at Negosyo', 'livelihood', 'Livelihood and business assistance program'),
        ('Emergency Response Program', 'emergency', 'Quick response for calamity victims'),
    ]
    
    for name, program_type, description in program_list:
        program = ServiceProgram.objects.create(
            name=name,
            program_type=program_type,
            description=description,
            objectives='To provide assistance and support to constituents in need',
            eligibility_criteria='Must be a resident of the district',
            required_documents='Valid ID, Proof of residence',
            target_beneficiaries='Indigent families and individuals',
            start_date=datetime.now().date() - timedelta(days=90),
            application_start=datetime.now().date() - timedelta(days=60),
            total_budget=random.randint(500000, 2000000),
            max_beneficiaries=random.randint(100, 500),
            status='active',
            published_at=timezone.now()
        )
        programs.append(program)
    
    print(f"Created {ServiceProgram.objects.count()} service programs")
    return programs

def create_referrals(users, services):
    """Create test referrals."""
    print("Creating referrals...")
    
    referrals = []
    status_choices = ['pending', 'in_progress', 'resolved', 'closed']
    
    for _ in range(100):
        constituent = random.choice(Constituent.objects.all())
        service = random.choice(services)
        
        referral = Referral.objects.create(
            constituent=constituent,
            service=service,
            description=f'Request for {service.name}',
            urgency='normal',
            status=random.choice(status_choices),
            staff_assigned=random.choice(users['staff']) if random.choice([True, False]) else None,
            resolution_notes='Case resolved successfully' if random.choice([True, False]) else ''
        )
        
        # Add random dates
        referral.created_at = timezone.now() - timedelta(days=random.randint(1, 90))
        if referral.status in ['resolved', 'closed']:
            referral.resolved_at = referral.created_at + timedelta(days=random.randint(1, 14))
        referral.save()
        
        referrals.append(referral)
    
    print(f"Created {Referral.objects.count()} referrals")
    return referrals

def create_service_applications(users, programs):
    """Create test service applications."""
    print("Creating service applications...")
    
    applications = []
    
    for _ in range(50):
        program = random.choice(programs)
        applicant = random.choice(users['constituents'])
        
        application = ServiceApplication.objects.create(
            program=program,
            applicant=applicant,
            beneficiary_is_self=True,
            household_size=random.randint(1, 8),
            household_income=random.randint(5000, 20000),
            reason_for_application='Need assistance for family',
            supporting_details='Additional information about the application',
            priority_level=random.choice(['low', 'normal', 'high', 'urgent']),
            status=random.choice(['submitted', 'under_review', 'approved', 'rejected']),
            submitted_at=timezone.now() - timedelta(days=random.randint(1, 30))
        )
        
        applications.append(application)
    
    print(f"Created {ServiceApplication.objects.count()} service applications")
    return applications

def main():
    """Main function to create all test data."""
    print("Starting test data creation...")
    
    # Clear existing data
    print("Clearing existing data...")
    User.objects.all().delete()
    
    # Create data
    users = create_users()
    chapters = create_chapters(users)
    services = create_services()
    programs = create_service_programs()
    referrals = create_referrals(users, services)
    applications = create_service_applications(users, programs)
    
    print("\nTest data creation completed!")
    print(f"Total users: {User.objects.count()}")
    print(f"Total chapters: {Chapter.objects.count()}")
    print(f"Total services: {Service.objects.count()}")
    print(f"Total programs: {ServiceProgram.objects.count()}")
    print(f"Total referrals: {Referral.objects.count()}")
    print(f"Total applications: {ServiceApplication.objects.count()}")
    
    print("\nTest credentials:")
    print("MP: mp_fahanie / Test@Pass123!")
    print("Staff: staff1 / Test@Pass123!")
    print("Coordinator: coord_alicia / Test@Pass123!")
    print("Member: member1 / Test@Pass123!")
    print("Constituent: constituent1 / Test@Pass123!")

if __name__ == '__main__':
    main()