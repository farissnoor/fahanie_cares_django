from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser for development'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@fahaniecares.gov.ph',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS('Created superuser: admin'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists'))