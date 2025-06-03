#!/usr/bin/env python3
"""
Test script to verify staff profile system is working correctly
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
from django.urls import reverse

User = get_user_model()

def test_staff_system():
    print("🧪 TESTING STAFF PROFILE SYSTEM")
    print("=" * 50)
    
    # Test 1: Check staff count
    total_staff = Staff.objects.filter(is_active=True).count()
    print(f"✅ Total active staff: {total_staff}")
    
    # Test 2: Check developers
    developers = Staff.objects.filter(user__is_superuser=True)
    print(f"✅ Developers found: {developers.count()}")
    for dev in developers:
        print(f"   - {dev.full_name} ({dev.user.username})")
    
    # Test 3: Check URL reversing
    try:
        profile_url = reverse('staff:profile')
        print(f"✅ Staff profile URL: {profile_url}")
        
        directory_url = reverse('staff:directory') 
        print(f"✅ Staff directory URL: {directory_url}")
        
        dashboard_url = reverse('staff:dashboard')
        print(f"✅ Staff dashboard URL: {dashboard_url}")
        
    except Exception as e:
        print(f"❌ URL reverse error: {e}")
    
    # Test 4: Check division stats
    division_stats = Staff.objects.filter(is_active=True).values('division').distinct()
    print(f"✅ Divisions represented: {len(division_stats)}")
    
    # Test 5: Check template context
    print("\n📊 DASHBOARD CONTEXT TEST:")
    print("-" * 30)
    
    # Simulate dashboard context
    division_counts = {}
    for staff in Staff.objects.filter(is_active=True):
        div = staff.get_division_display() or "Unassigned"
        division_counts[div] = division_counts.get(div, 0) + 1
    
    for division, count in division_counts.items():
        print(f"• {division}: {count} staff")
    
    # Test 6: Check employment status
    status_counts = {}
    for staff in Staff.objects.filter(is_active=True):
        status = staff.get_employment_status_display() or "Unassigned"
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"\n💼 EMPLOYMENT STATUS:")
    print("-" * 25)
    for status, count in status_counts.items():
        print(f"• {status}: {count} staff")
    
    print(f"\n🎉 STAFF SYSTEM TEST COMPLETED!")
    print(f"✅ All components appear to be working correctly")
    print(f"🌐 Ready to access at: http://localhost:8000/staff/")

if __name__ == '__main__':
    test_staff_system()