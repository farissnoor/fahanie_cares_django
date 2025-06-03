"""
Management command to set up ministry-specific permissions and groups.
Run this command after initial deployment to configure role-based access.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.services.models import MinistryProgram
from apps.services.permissions import MinistryGroupManager


class Command(BaseCommand):
    help = 'Set up ministry-specific user groups and permissions for role-based access control'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of groups even if they exist',
        )
        
        parser.add_argument(
            '--ministry',
            type=str,
            help='Set up permissions for specific ministry only',
            choices=[choice[0] for choice in MinistryProgram.MINISTRIES],
        )
        
        parser.add_argument(
            '--list-groups',
            action='store_true',
            help='List all ministry groups that will be created',
        )
    
    def handle(self, *args, **options):
        if options['list_groups']:
            self.list_ministry_groups()
            return
        
        self.stdout.write(
            self.style.SUCCESS('Setting up ministry permissions and groups...')
        )
        
        # Create or update groups
        try:
            groups_created = self.create_ministry_groups(
                force=options['force'],
                ministry=options.get('ministry')
            )
            
            # Set up permissions
            self.setup_permissions()
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully set up ministry permissions!'
                )
            )
            
            if groups_created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created {len(groups_created)} new groups:'
                    )
                )
                for group in groups_created:
                    self.stdout.write(f'  - {group}')
            else:
                self.stdout.write(
                    self.style.WARNING('No new groups were created (all existed)')
                )
            
        except Exception as e:
            raise CommandError(f'Failed to set up permissions: {str(e)}')
    
    def list_ministry_groups(self):
        """List all ministry groups that would be created."""
        self.stdout.write(
            self.style.HTTP_INFO('Ministry groups that will be created:')
        )
        
        from apps.services.permissions import MinistryProgramPermissions
        
        for ministry, roles in MinistryProgramPermissions.MINISTRY_LIAISONS.items():
            ministry_name = dict(MinistryProgram.MINISTRIES)[ministry]
            self.stdout.write(f'\n{ministry_name} ({ministry}):')
            
            for role in roles:
                self.stdout.write(f'  - {role}')
    
    def create_ministry_groups(self, force=False, ministry=None):
        """Create ministry-specific user groups."""
        from apps.services.permissions import MinistryProgramPermissions
        
        groups_created = []
        
        ministries_to_process = (
            {ministry: MinistryProgramPermissions.MINISTRY_LIAISONS[ministry]}
            if ministry else MinistryProgramPermissions.MINISTRY_LIAISONS
        )
        
        for ministry_code, roles in ministries_to_process.items():
            ministry_name = dict(MinistryProgram.MINISTRIES)[ministry_code]
            
            self.stdout.write(
                f'Processing {ministry_name} ({ministry_code})...'
            )
            
            for role in roles:
                group, created = Group.objects.get_or_create(name=role)
                
                if created or force:
                    groups_created.append(role)
                    self.stdout.write(
                        f'  ✓ Created group: {role}'
                    )
                else:
                    self.stdout.write(
                        f'  - Group exists: {role}'
                    )
        
        return groups_created
    
    def setup_permissions(self):
        """Set up Django permissions for ministry programs."""
        self.stdout.write('Setting up Django permissions...')
        
        # Get content type for MinistryProgram
        content_type = ContentType.objects.get_for_model(MinistryProgram)
        
        # Define custom permissions
        custom_permissions = [
            ('view_ministry_program', 'Can view ministry program'),
            ('add_ministry_program', 'Can add ministry program'),
            ('change_ministry_program', 'Can change ministry program'),
            ('delete_ministry_program', 'Can delete ministry program'),
            ('approve_ministry_program', 'Can approve ministry program'),
            ('export_ministry_programs', 'Can export ministry programs'),
            ('view_program_history', 'Can view program history'),
            ('manage_program_budget', 'Can manage program budget'),
            ('assign_program_staff', 'Can assign program staff'),
        ]
        
        permissions_created = []
        
        for codename, name in custom_permissions:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            
            if created:
                permissions_created.append(permission.name)
                self.stdout.write(f'  ✓ Created permission: {name}')
            else:
                self.stdout.write(f'  - Permission exists: {name}')
        
        # Assign permissions to groups
        self.assign_permissions_to_groups()
        
        return permissions_created
    
    def assign_permissions_to_groups(self):
        """Assign appropriate permissions to ministry groups."""
        self.stdout.write('Assigning permissions to groups...')
        
        # Get all ministry program permissions
        content_type = ContentType.objects.get_for_model(MinistryProgram)
        all_permissions = Permission.objects.filter(content_type=content_type)
        
        # Liaison permissions (full access to their ministry)
        liaison_permissions = all_permissions.filter(
            codename__in=[
                'view_ministry_program',
                'add_ministry_program', 
                'change_ministry_program',
                'approve_ministry_program',
                'view_program_history',
                'manage_program_budget',
                'assign_program_staff',
            ]
        )
        
        # Coordinator permissions (limited access)
        coordinator_permissions = all_permissions.filter(
            codename__in=[
                'view_ministry_program',
                'add_ministry_program',
                'change_ministry_program',
                'view_program_history',
            ]
        )
        
        # Assign permissions based on role type
        from apps.services.permissions import MinistryProgramPermissions
        
        for ministry, roles in MinistryProgramPermissions.MINISTRY_LIAISONS.items():
            ministry_name = dict(MinistryProgram.MINISTRIES)[ministry]
            
            for i, role in enumerate(roles):
                try:
                    group = Group.objects.get(name=role)
                    
                    if i == 0:  # Primary role (liaison)
                        group.permissions.set(liaison_permissions)
                        permission_type = "liaison"
                    else:  # Secondary role (coordinator)
                        group.permissions.set(coordinator_permissions)
                        permission_type = "coordinator"
                    
                    self.stdout.write(
                        f'  ✓ Assigned {permission_type} permissions to {role}'
                    )
                    
                except Group.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  ! Group not found: {role}')
                    )
    
    def get_group_summary(self):
        """Get summary of created groups and their permissions."""
        from apps.services.permissions import MinistryProgramPermissions
        
        summary = {}
        
        for ministry, roles in MinistryProgramPermissions.MINISTRY_LIAISONS.items():
            ministry_name = dict(MinistryProgram.MINISTRIES)[ministry]
            summary[ministry_name] = []
            
            for role in roles:
                try:
                    group = Group.objects.get(name=role)
                    permission_count = group.permissions.count()
                    summary[ministry_name].append({
                        'role': role,
                        'permissions': permission_count,
                        'exists': True
                    })
                except Group.DoesNotExist:
                    summary[ministry_name].append({
                        'role': role,
                        'permissions': 0,
                        'exists': False
                    })
        
        return summary