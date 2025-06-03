from django.utils import timezone
from apps.chapters.models import Chapter
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()

# Get the first admin user for coordinator
admin_user = User.objects.filter(is_staff=True).first()

# Barangays by municipality
barangays = {
    'Datu Piang': [
        'Balong', 'Buayan', 'Damabalas', 'Damalusay', 'Dulawan', 
        'Kanguan', 'Kalipapa', 'Liong', 'Magaslong', 'Montay', 'Poblacion'
    ],
    'Datu Saudi-Ampatuan': [
        'Dapiawan', 'Elian', 'Gawang', 'Kabengi', 'Kitango', 
        'Kitapok', 'Madia', 'Pagatin', 'Poblacion', 'Salbu'
    ],
    'Datu Salibo': [
        'Andavit', 'Butilen', 'Pagatin I', 'Pagatin II', 'Pagatin III', 
        'Pandi', 'Sambulawan', 'Saniag'
    ],
    'Shariff Saydona Mustapha': [
        'Bakat', 'Nabundas', 'Linantangan', 'Pagatin IV', 'Pamalian',
        'Dapiawan', 'Ganta', 'Libutan', 'Tina', 'Poblacion'
    ],
    'Mamasapano': [
        'Bagumbong', 'Dabenayan', 'Daladap', 'Dasikil', 'Liab', 
        'Lusay', 'Mamasapano', 'Manongkaling', 'Pimbalakan', 'Sapakan', 'Tuka'
    ],
    'Shariff Aguak': [
        'Bialong', 'Lapok', 'Lepok', 'Malingao', 'Poblacion', 
        'Poblacion III', 'Tapikan', 'Taib'
    ],
    'Datu Unsay': [
        'Maitumaig', 'Meta', 'Pamalian', 'Poblacion', 'Tuntungan'
    ]
}

# Create barangay chapters
created_count = 0
for municipality, brgy_list in barangays.items():
    # Get the municipal chapter
    municipal_chapter = Chapter.objects.filter(
        name__contains=municipality, 
        tier='municipal'
    ).first()
    
    if not municipal_chapter:
        print(f"Municipal chapter for {municipality} not found. Skipping barangays.")
        continue
    
    # Create barangay chapters
    for barangay in brgy_list:
        chapter_name = f"{barangay}, {municipality} Barangay Chapter"
        
        chapter, created = Chapter.objects.get_or_create(
            name=chapter_name,
            defaults={
                'slug': slugify(chapter_name),
                'tier': 'barangay',
                'municipality': municipality,
                'province': 'Maguindanao del Sur',
                'description': f"The {barangay} Barangay Chapter of #FahanieCares, serving the residents of Barangay {barangay} in {municipality}, Maguindanao del Sur.",
                'mission_statement': f"To bring public service closer to the residents of Barangay {barangay} through community-based initiatives and programs.",
                'established_date': timezone.now().date(),
                'status': 'active',
                'coordinator': admin_user,
                'parent_chapter': municipal_chapter,
                'email': f"{slugify(barangay)}.{slugify(municipality)}@fahaniecares.org",
                'phone': '+63 XXX XXX XXXX',
            }
        )
        
        if created:
            created_count += 1
            print(f"Created barangay chapter: {chapter.name}")
        else:
            print(f"Barangay chapter already exists: {chapter.name}")

print(f"\nCreated {created_count} new barangay chapters.")