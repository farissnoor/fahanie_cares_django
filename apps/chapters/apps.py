from django.apps import AppConfig


class ChaptersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.chapters'
    label = 'chapters'
    verbose_name = 'Chapter Management'
