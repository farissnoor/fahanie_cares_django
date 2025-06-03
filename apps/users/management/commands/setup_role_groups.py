"""
Management command to set up Django Groups for role hierarchy.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction


class Command(BaseCommand):
    help = 'Set up Django Groups for #FahanieCares role hierarchy'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all groups and recreate them',
        )
    
    def handle(self, *args, **options):
        """Set up role groups with appropriate permissions."""
        
        if options['reset']:
            self.stdout.write('Resetting all role groups...')
            Group.objects.filter(
                name__in=['Member', 'Chapter Member', 'Chapter Coordinator', 'Referral Staff', 'Program Admin', 'Superadmin']
            ).delete()
        
        with transaction.atomic():
            self._create_role_groups()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up role groups!')
        )
    
    def _create_role_groups(self):
        """Create Django Groups for each role with appropriate permissions."""
        
        # Define roles and their permissions
        role_permissions = {
            'Member': [
                # Referral permissions
                ('referrals', 'referral', 'view_referral'),
                ('referrals', 'referral', 'add_referral'),
                # Program permissions
                ('services', 'program', 'view_program'),
                # Chapter permissions
                ('chapters', 'chapter', 'view_chapter'),
            ],
            'Chapter Member': [
                # All Member permissions plus:
                ('referrals', 'referral', 'view_referral'),
                ('referrals', 'referral', 'add_referral'),
                ('services', 'program', 'view_program'),
                ('chapters', 'chapter', 'view_chapter'),
                # Constituent permissions
                ('constituents', 'constituent', 'add_constituent'),
                ('constituents', 'constituent', 'view_constituent'),
            ],
            'Chapter Coordinator': [
                # All Chapter Member permissions plus:
                ('referrals', 'referral', 'view_referral'),
                ('referrals', 'referral', 'add_referral'),
                ('referrals', 'referral', 'change_referral'),
                ('services', 'program', 'view_program'),
                ('chapters', 'chapter', 'view_chapter'),
                ('chapters', 'chapter', 'change_chapter'),
                ('constituents', 'constituent', 'add_constituent'),
                ('constituents', 'constituent', 'change_constituent'),
                ('constituents', 'constituent', 'view_constituent'),
                # User permissions for chapter members
                ('users', 'user', 'add_user'),
                ('users', 'user', 'view_user'),
            ],
            'Referral Staff': [
                # Referral management
                ('referrals', 'referral', 'view_referral'),
                ('referrals', 'referral', 'add_referral'),
                ('referrals', 'referral', 'change_referral'),
                ('referrals', 'referral', 'delete_referral'),
                # Program access
                ('services', 'program', 'view_program'),
                # Chapter access
                ('chapters', 'chapter', 'view_chapter'),
                # Constituent management
                ('constituents', 'constituent', 'view_constituent'),
                ('constituents', 'constituent', 'change_constituent'),
                # User viewing
                ('users', 'user', 'view_user'),
                # Document management
                ('documents', 'document', 'view_document'),
                ('documents', 'document', 'add_document'),
                ('documents', 'document', 'change_document'),
            ],
            'Program Admin': [
                # Program management
                ('services', 'program', 'view_program'),
                ('services', 'program', 'add_program'),
                ('services', 'program', 'change_program'),
                ('services', 'program', 'delete_program'),
                # Referral access
                ('referrals', 'referral', 'view_referral'),
                ('referrals', 'referral', 'change_referral'),
                # Chapter management
                ('chapters', 'chapter', 'view_chapter'),
                ('chapters', 'chapter', 'change_chapter'),
                # Constituent management
                ('constituents', 'constituent', 'view_constituent'),
                ('constituents', 'constituent', 'change_constituent'),
                # User management
                ('users', 'user', 'view_user'),
                ('users', 'user', 'change_user'),
            ],
            'Superadmin': [
                # All permissions will be granted via is_superuser
                # This group exists for organization but superusers bypass group permissions
            ],
        }
        
        # Create groups and assign permissions
        for role_name, permission_tuples in role_permissions.items():
            group, created = Group.objects.get_or_create(name=role_name)
            
            if created:
                self.stdout.write(f'Created group: {role_name}')
            else:
                self.stdout.write(f'Group already exists: {role_name}')
                # Clear existing permissions
                group.permissions.clear()
            
            # Add permissions to group
            permissions_added = 0
            for app_label, model_name, permission_codename in permission_tuples:
                try:
                    content_type = ContentType.objects.get(
                        app_label=app_label,
                        model=model_name
                    )
                    permission = Permission.objects.get(
                        content_type=content_type,
                        codename=permission_codename
                    )
                    group.permissions.add(permission)
                    permissions_added += 1
                except (ContentType.DoesNotExist, Permission.DoesNotExist):
                    self.stdout.write(
                        self.style.WARNING(
                            f'Permission not found: {app_label}.{permission_codename}'
                        )
                    )
            
            self.stdout.write(f'  Added {permissions_added} permissions to {role_name}')
        
        # Create additional custom permissions
        self._create_custom_permissions()
    
    def _create_custom_permissions(self):
        """Create custom permissions that don't exist in standard Django models."""
        
        custom_permissions = [
            # Feature-based permissions
            ('users', 'user', 'can_manage_referrals', 'Can manage referral system'),
            ('users', 'user', 'can_view_analytics', 'Can view system analytics'),
            ('users', 'user', 'can_manage_chapters', 'Can manage chapters'),
            ('users', 'user', 'can_approve_members', 'Can approve new members'),
            ('users', 'user', 'can_send_notifications', 'Can send system notifications'),
            ('users', 'user', 'can_manage_documents', 'Can manage document system'),
            ('users', 'user', 'can_system_admin', 'Can perform system administration'),
        ]
        
        for app_label, model_name, codename, name in custom_permissions:
            try:
                content_type = ContentType.objects.get(
                    app_label=app_label,
                    model=model_name
                )
                permission, created = Permission.objects.get_or_create(
                    content_type=content_type,
                    codename=codename,
                    defaults={'name': name}
                )
                if created:
                    self.stdout.write(f'Created custom permission: {codename}')
            except ContentType.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'Content type not found for: {app_label}.{model_name}'
                    )
                )