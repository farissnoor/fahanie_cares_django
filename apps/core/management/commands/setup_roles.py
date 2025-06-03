"""
Setup role-based groups and permissions for unified interface
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

class Command(BaseCommand):
    help = 'Set up role-based groups and permissions'
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up role groups...')
        
        # Define role hierarchy
        roles = {
            'member': {
                'description': 'Registered Members',
                'permissions': [
                    ('constituents', 'view_constituent', 'Can view constituent'),
                    ('constituents', 'add_constituent', 'Can add constituent'),
                    ('constituents', 'change_constituent', 'Can change constituent'),
                    ('referrals', 'add_referral', 'Can add referral'),
                    ('referrals', 'view_referral', 'Can view referral'),
                    ('chapters', 'view_chapter', 'Can view chapter'),
                ]
            },
            'referral_staff': {
                'description': 'Referral Processing Staff',
                'inherits': 'member',
                'permissions': [
                    ('referrals', 'change_referral', 'Can change referral'),
                    ('referrals', 'process_referral', 'Can process referrals'),
                    ('referrals', 'view_all_referrals', 'Can view all referrals'),
                    ('analytics', 'view_referral_analytics', 'Can view referral analytics'),
                ]
            },
            'program_admin': {
                'description': 'Program Administration Staff',
                'inherits': 'referral_staff',
                'permissions': [
                    ('services', 'add_ministryprogram', 'Can add ministry program'),
                    ('services', 'change_ministryprogram', 'Can change ministry program'),
                    ('services', 'delete_ministryprogram', 'Can delete ministry program'),
                    ('services', 'manage_program_budget', 'Can manage program budget'),
                    ('analytics', 'view_program_analytics', 'Can view program analytics'),
                ]
            }
        }
        
        with transaction.atomic():
            created_groups = {}
            
            # Create groups
            for role_name, role_config in roles.items():
                group, created = Group.objects.get_or_create(name=role_name)
                created_groups[role_name] = group
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created group: {role_name}')
                    )
                else:
                    self.stdout.write(f'Group already exists: {role_name}')
                
                # Add permissions
                for app_label, codename, name in role_config.get('permissions', []):
                    try:
                        # Try to get existing permission
                        content_type = ContentType.objects.get(app_label=app_label)
                        permission, perm_created = Permission.objects.get_or_create(
                            codename=codename,
                            content_type=content_type,
                            defaults={'name': name}
                        )
                        
                        group.permissions.add(permission)
                        
                        if perm_created:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  Created permission: {app_label}.{codename}'
                                )
                            )
                    except ContentType.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  App not found: {app_label} (will be available after migrations)'
                            )
                        )
                
                # Handle inheritance
                if 'inherits' in role_config:
                    parent_group = created_groups.get(role_config['inherits'])
                    if parent_group:
                        # Add parent group permissions to current group
                        parent_perms = parent_group.permissions.all()
                        group.permissions.add(*parent_perms)
                        self.stdout.write(
                            f'  Inherited {parent_perms.count()} permissions from {role_config["inherits"]}'
                        )
        
        self.stdout.write(
            self.style.SUCCESS('Role groups setup completed!')
        )
