from django.apps import AppConfig


class ConstituentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.constituents'
    label = 'constituents'
    verbose_name = 'Constituent Management'
