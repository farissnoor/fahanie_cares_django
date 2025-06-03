from django.utils import timezone
from apps.chapters.models import Chapter
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()

# Get the first admin user for coordinator
admin_user = User.objects.filter(is_staff=True).first()

# Create provincial chapter first
provincial_chapter, created = Chapter.objects.get_or_create(
    name="Maguindanao del Sur Provincial Chapter",
    defaults={
        'slug': slugify("Maguindanao del Sur Provincial Chapter"),
        'tier': 'provincial',
        'municipality': 'Buluan',
        'province': 'Maguindanao del Sur',
        'description': "The provincial chapter of #FahanieCares in Maguindanao del Sur, focusing on serving communities across the province.",
        'mission_statement': "To bring quality public service and community support to all municipalities of Maguindanao del Sur.",
        'established_date': timezone.now().date(),
        'status': 'active',
        'coordinator': admin_user,
        'email': 'maguindanaosur@fahaniecares.org',
        'phone': '+63 XXX XXX XXXX',
    }
)
print(f"Provincial chapter: {provincial_chapter.name} ({'created' if created else 'already exists'})")

# List of municipalities in 2nd Parliamentary District of Maguindanao del Sur
municipalities = [
    {
        'name': 'Datu Piang',
        'description': "The Datu Piang chapter of #FahanieCares, focusing on local community development and assistance programs.",
    },
    {
        'name': 'Datu Saudi-Ampatuan',
        'description': "The Datu Saudi-Ampatuan chapter of #FahanieCares, working to address local needs and improve community services.",
    },
    {
        'name': 'Datu Salibo',
        'description': "The Datu Salibo chapter of #FahanieCares, promoting education, healthcare, and social welfare initiatives.",
    },
    {
        'name': 'Shariff Saydona Mustapha',
        'description': "The Shariff Saydona Mustapha chapter of #FahanieCares, advocating for sustainable development and community empowerment.",
    },
    {
        'name': 'Mamasapano',
        'description': "The Mamasapano chapter of #FahanieCares, focusing on peace-building, reconciliation, and community support.",
    },
    {
        'name': 'Shariff Aguak',
        'description': "The Shariff Aguak chapter of #FahanieCares, formerly known as Maganoy, working on public service initiatives.",
    },
    {
        'name': 'Datu Unsay',
        'description': "The Datu Unsay chapter of #FahanieCares, delivering community services and support programs.",
    }
]

# Create a municipal chapter for each municipality
for municipality in municipalities:
    chapter_name = f"{municipality['name']} Municipal Chapter"
    
    chapter, created = Chapter.objects.get_or_create(
        name=chapter_name,
        defaults={
            'slug': slugify(chapter_name),
            'tier': 'municipal',
            'municipality': municipality['name'],
            'province': 'Maguindanao del Sur',
            'description': municipality['description'],
            'mission_statement': f"To uplift the lives of residents in {municipality['name']} through responsive and inclusive public service.",
            'established_date': timezone.now().date(),
            'status': 'active',
            'coordinator': admin_user,
            'parent_chapter': provincial_chapter,
            'email': f"{municipality['name'].lower().replace(' ', '')}@fahaniecares.org",
            'phone': '+63 XXX XXX XXXX',
        }
    )
    print(f"Municipal chapter: {chapter.name} ({'created' if created else 'already exists'})")

print("\nAll chapters for 2nd Parliamentary District of Maguindanao del Sur have been created.")