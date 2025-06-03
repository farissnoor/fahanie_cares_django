#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.users.models import User

def create_demo_users():
    # Create Staff User
    staff_user, created = User.objects.get_or_create(
        username='staff_demo',
        defaults={
            'email': 'staff@fahaniecares.com',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'user_type': 'staff',
            'is_staff': True,
            'is_active': True,
        }
    )
    if created:
        staff_user.set_password('staff123')
        staff_user.save()
        print(f"✓ Staff user created:")
        print(f"  Username: staff_demo")
        print(f"  Password: staff123")
        print(f"  Email: staff@fahaniecares.com")
        print(f"  Type: {staff_user.user_type}")
    else:
        print(f"Staff user already exists: {staff_user.username}")

    # Create Member User
    member_user, created = User.objects.get_or_create(
        username='member_demo',
        defaults={
            'email': 'member@fahaniecares.com',
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'user_type': 'member',
            'is_active': True,
        }
    )
    if created:
        member_user.set_password('member123')
        member_user.save()
        print(f"✓ Member user created:")
        print(f"  Username: member_demo")
        print(f"  Password: member123")
        print(f"  Email: member@fahaniecares.com")
        print(f"  Type: {member_user.user_type}")
    else:
        print(f"Member user already exists: {member_user.username}")

    # Create Constituent User
    constituent_user, created = User.objects.get_or_create(
        username='constituent_demo',
        defaults={
            'email': 'constituent@fahaniecares.com',
            'first_name': 'Ana',
            'last_name': 'Reyes',
            'user_type': 'constituent',
            'is_active': True,
        }
    )
    if created:
        constituent_user.set_password('constituent123')
        constituent_user.save()
        print(f"✓ Constituent user created:")
        print(f"  Username: constituent_demo")
        print(f"  Password: constituent123")
        print(f"  Email: constituent@fahaniecares.com")
        print(f"  Type: {constituent_user.user_type}")
    else:
        print(f"Constituent user already exists: {constituent_user.username}")

    print("\n" + "="*50)
    print("DEMO USERS SUMMARY")
    print("="*50)
    print("1. ADMIN USER (existing):")
    print("   Username: admin")
    print("   Password: admin123")
    print("   Access: Django Admin + All interfaces")
    print()
    print("2. STAFF USER:")
    print("   Username: staff_demo")
    print("   Password: staff123")
    print("   Access: Staff Dashboard + Public")
    print()
    print("3. MEMBER USER:")
    print("   Username: member_demo")
    print("   Password: member123")
    print("   Access: Member Features + Public")
    print()
    print("4. CONSTITUENT USER:")
    print("   Username: constituent_demo")
    print("   Password: constituent123")
    print("   Access: Public interface only")

if __name__ == '__main__':
    create_demo_users()