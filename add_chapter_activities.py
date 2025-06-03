from django.utils import timezone
from apps.chapters.models import Chapter, ChapterActivity
from django.contrib.auth import get_user_model
import random
from datetime import timedelta

User = get_user_model()

# Get the first admin user as organizer
admin_user = User.objects.filter(is_staff=True).first()

# Sample activity types and titles
ACTIVITY_TYPES = [
    'meeting', 'outreach', 'fundraising', 'training', 
    'social', 'volunteer', 'campaign'
]

ACTIVITY_TEMPLATES = [
    {
        'type': 'outreach',
        'title_template': "{} Medical Mission",
        'description': "Free medical check-ups, consultations, and medicine distribution for the residents.",
        'objectives': "To provide basic healthcare services to underserved communities and promote health awareness."
    },
    {
        'type': 'training',
        'title_template': "{} Skills Training Workshop",
        'description': "Training on livelihood skills including crafts, food processing, and digital literacy.",
        'objectives': "To enhance employability and entrepreneurial skills of community members."
    },
    {
        'type': 'meeting',
        'title_template': "{} Monthly Chapter Meeting",
        'description': "Regular meeting of chapter members to discuss ongoing programs and upcoming activities.",
        'objectives': "To coordinate chapter activities and ensure alignment with #FahanieCares mission."
    },
    {
        'type': 'volunteer',
        'title_template': "{} Community Clean-up Drive",
        'description': "Volunteer activity focused on cleaning public spaces and promoting environmental awareness.",
        'objectives': "To improve community sanitation and foster environmental stewardship."
    },
    {
        'type': 'campaign',
        'title_template': "{} Education Awareness Campaign",
        'description': "Information campaign about educational opportunities and scholarship programs.",
        'objectives': "To increase awareness about educational resources and support available to the community."
    }
]

# Get all municipal chapters
municipal_chapters = Chapter.objects.filter(tier='municipal')

activities_created = 0

# Create activities for each municipal chapter
for chapter in municipal_chapters:
    # Create 2-3 activities per municipal chapter
    num_activities = random.randint(2, 3)
    
    for i in range(num_activities):
        # Select a random activity template
        template = random.choice(ACTIVITY_TEMPLATES)
        
        # Generate random date within the last 60 days
        random_days = random.randint(1, 60)
        activity_date = (timezone.now() - timedelta(days=random_days)).date()
        
        # Create the activity
        title = template['title_template'].format(chapter.municipality)
        
        activity = ChapterActivity.objects.create(
            chapter=chapter,
            title=title,
            activity_type=template['type'],
            description=template['description'],
            objectives=template['objectives'],
            date=activity_date,
            start_time=timezone.now().replace(hour=9, minute=0, second=0, microsecond=0).time(),
            end_time=timezone.now().replace(hour=16, minute=0, second=0, microsecond=0).time(),
            status='completed',
            venue=f"{chapter.municipality} Community Center",
            address=f"Poblacion, {chapter.municipality}, {chapter.province}",
            organizer=admin_user,
            target_participants=random.randint(30, 100),
            actual_participants=random.randint(20, 80),
            budget=random.randint(5000, 20000),
            actual_cost=random.randint(4000, 18000),
        )
        
        activities_created += 1
        print(f"Created activity: {activity.title} for {chapter.name}")

print(f"\nCreated {activities_created} new chapter activities.")