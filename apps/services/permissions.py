"""
Role-based permissions for Ministry Programs.
Implements fine-grained access control for different user types.
"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from functools import wraps
from .models import MinistryProgram


class MinistryProgramPermissions:
    """
    Centralized permissions management for Ministry Programs.
    Handles role-based access control for CRUD operations.
    """
    
    # User type hierarchy (higher value = more permissions)
    USER_TYPE_HIERARCHY = {
        'constituent': 1,
        'member': 2,
        'chapter_member': 3,
        'coordinator': 4,
        'staff': 5,
        'mp': 6,
    }
    
    # Ministry-specific permissions mapping
    MINISTRY_LIAISONS = {
        'mssd': ['mssd_liaison', 'social_services_coordinator'],
        'mafar': ['mafar_liaison', 'agriculture_coordinator'],
        'mtit': ['mtit_liaison', 'trade_coordinator'],
        'mhe': ['education_liaison', 'higher_ed_coordinator'],
        'mbasiced': ['basiced_liaison', 'basic_ed_coordinator'],
        'moh': ['health_liaison', 'health_coordinator'],
        'mpwh': ['public_works_liaison', 'infrastructure_coordinator'],
        'motc': ['transport_liaison', 'transport_coordinator'],
        'mei': ['environment_liaison', 'environment_coordinator'],
        'mle': ['labor_liaison', 'employment_coordinator'],
    }
    
    @staticmethod
    def can_view_program(user, program):
        """Check if user can view a specific program."""
        if not user.is_authenticated:
            return program.is_public and not program.is_deleted
        
        if user.is_superuser:
            return True
        
        # MP can view all programs
        if user.user_type == 'mp':
            return True
        
        # Staff can view all programs
        if user.user_type == 'staff':
            return True
        
        # Program managers and liaisons can view their programs
        if user in [program.created_by, program.ministry_liaison, program.program_manager]:
            return True
        
        # Coordinators can view programs in their jurisdiction
        if user.user_type == 'coordinator':
            return True
        
        # Chapter members can view public programs
        if user.user_type in ['chapter_member', 'member']:
            return program.is_public and not program.is_deleted
        
        # Default: public programs only
        return program.is_public and not program.is_deleted
    
    @staticmethod
    def can_create_program(user, ministry=None):
        """Check if user can create programs for a specific ministry."""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # MP can create programs for any ministry
        if user.user_type == 'mp':
            return True
        
        # Staff can create programs
        if user.user_type == 'staff':
            return True
        
        # Coordinators can create programs for their ministries
        if user.user_type == 'coordinator' and ministry:
            # Check if user has permission for this ministry
            user_groups = user.groups.values_list('name', flat=True)
            ministry_roles = MinistryProgramPermissions.MINISTRY_LIAISONS.get(ministry, [])
            return any(role in user_groups for role in ministry_roles)
        
        return False
    
    @staticmethod
    def can_edit_program(user, program):
        """Check if user can edit a specific program."""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # Use the model's built-in permission check
        return program.can_edit(user)
    
    @staticmethod
    def can_delete_program(user, program):
        """Check if user can delete a specific program."""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # Use the model's built-in permission check
        return program.can_delete(user)
    
    @staticmethod
    def can_approve_program(user, program):
        """Check if user can approve a specific program."""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # MP can approve any program
        if user.user_type == 'mp':
            return True
        
        # Staff can approve programs
        if user.user_type == 'staff':
            return True
        
        # Ministry liaisons can approve their ministry's programs
        if user == program.ministry_liaison:
            return True
        
        return False
    
    @staticmethod
    def can_manage_ministry(user, ministry):
        """Check if user can manage programs for a specific ministry."""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # MP can manage all ministries
        if user.user_type == 'mp':
            return True
        
        # Staff can manage all ministries
        if user.user_type == 'staff':
            return True
        
        # Check if user has ministry-specific permissions
        user_groups = user.groups.values_list('name', flat=True)
        ministry_roles = MinistryProgramPermissions.MINISTRY_LIAISONS.get(ministry, [])
        return any(role in user_groups for role in ministry_roles)
    
    @staticmethod
    def can_export_programs(user):
        """Check if user can export program data."""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # Staff and above can export
        return user.user_type in ['staff', 'mp']
    
    @staticmethod
    def can_view_history(user, program):
        """Check if user can view program change history."""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # MP can view all history
        if user.user_type == 'mp':
            return True
        
        # Staff can view all history
        if user.user_type == 'staff':
            return True
        
        # Program stakeholders can view history
        if user in [program.created_by, program.ministry_liaison, program.program_manager]:
            return True
        
        return False
    
    @staticmethod
    def get_user_ministry_permissions(user):
        """Get list of ministries user has permissions for."""
        if not user.is_authenticated:
            return []
        
        if user.is_superuser or user.user_type in ['mp', 'staff']:
            return list(MinistryProgramPermissions.MINISTRY_LIAISONS.keys())
        
        user_groups = user.groups.values_list('name', flat=True)
        permitted_ministries = []
        
        for ministry, roles in MinistryProgramPermissions.MINISTRY_LIAISONS.items():
            if any(role in user_groups for role in roles):
                permitted_ministries.append(ministry)
        
        return permitted_ministries


# Decorators for view-level permissions
def require_program_view_permission(view_func):
    """Decorator to require view permission for a program."""
    @wraps(view_func)
    @login_required
    def wrapper(request, program_id=None, slug=None, *args, **kwargs):
        if program_id:
            program = get_object_or_404(MinistryProgram, id=program_id)
        elif slug:
            program = get_object_or_404(MinistryProgram, slug=slug)
        else:
            raise ValueError("Either program_id or slug must be provided")
        
        if not MinistryProgramPermissions.can_view_program(request.user, program):
            raise PermissionDenied("You don't have permission to view this program.")
        
        return view_func(request, program=program, *args, **kwargs)
    
    return wrapper


def require_program_edit_permission(view_func):
    """Decorator to require edit permission for a program."""
    @wraps(view_func)
    @login_required
    def wrapper(request, program_id=None, slug=None, *args, **kwargs):
        if program_id:
            program = get_object_or_404(MinistryProgram, id=program_id)
        elif slug:
            program = get_object_or_404(MinistryProgram, slug=slug)
        else:
            raise ValueError("Either program_id or slug must be provided")
        
        if not MinistryProgramPermissions.can_edit_program(request.user, program):
            raise PermissionDenied("You don't have permission to edit this program.")
        
        return view_func(request, program=program, *args, **kwargs)
    
    return wrapper


def require_program_delete_permission(view_func):
    """Decorator to require delete permission for a program."""
    @wraps(view_func)
    @login_required
    def wrapper(request, program_id=None, slug=None, *args, **kwargs):
        if program_id:
            program = get_object_or_404(MinistryProgram, id=program_id)
        elif slug:
            program = get_object_or_404(MinistryProgram, slug=slug)
        else:
            raise ValueError("Either program_id or slug must be provided")
        
        if not MinistryProgramPermissions.can_delete_program(request.user, program):
            raise PermissionDenied("You don't have permission to delete this program.")
        
        return view_func(request, program=program, *args, **kwargs)
    
    return wrapper


def require_ministry_permission(ministry):
    """Decorator to require permission for a specific ministry."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not MinistryProgramPermissions.can_manage_ministry(request.user, ministry):
                raise PermissionDenied(f"You don't have permission to manage {ministry} programs.")
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator


def require_export_permission(view_func):
    """Decorator to require export permission."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not MinistryProgramPermissions.can_export_programs(request.user):
            raise PermissionDenied("You don't have permission to export program data.")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


# Context processors for templates
def ministry_permissions_context(request):
    """Context processor to add ministry permissions to template context."""
    if request.user.is_authenticated:
        return {
            'user_ministry_permissions': MinistryProgramPermissions.get_user_ministry_permissions(request.user),
            'can_export_programs': MinistryProgramPermissions.can_export_programs(request.user),
        }
    return {}


# Management command helpers
class MinistryGroupManager:
    """Helper class for managing ministry-specific user groups."""
    
    @staticmethod
    def create_ministry_groups():
        """Create all ministry-specific groups."""
        from django.contrib.auth.models import Group, Permission
        
        groups_created = []
        
        for ministry, roles in MinistryProgramPermissions.MINISTRY_LIAISONS.items():
            ministry_name = dict(MinistryProgram.MINISTRIES)[ministry]
            
            for role in roles:
                group, created = Group.objects.get_or_create(
                    name=role,
                    defaults={'name': role}
                )
                
                if created:
                    groups_created.append(group.name)
                    
                    # Add relevant permissions to the group
                    permissions = Permission.objects.filter(
                        content_type__app_label='services',
                        content_type__model='ministryprogram'
                    )
                    
                    group.permissions.set(permissions)
        
        return groups_created
    
    @staticmethod
    def assign_user_to_ministry(user, ministry, role_type='liaison'):
        """Assign a user to a ministry with specified role."""
        from django.contrib.auth.models import Group
        
        ministry_roles = MinistryProgramPermissions.MINISTRY_LIAISONS.get(ministry, [])
        
        if role_type == 'liaison' and ministry_roles:
            group_name = ministry_roles[0]  # Primary liaison role
        elif role_type == 'coordinator' and len(ministry_roles) > 1:
            group_name = ministry_roles[1]  # Coordinator role
        else:
            raise ValueError(f"Invalid role type '{role_type}' for ministry '{ministry}'")
        
        try:
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            return True
        except Group.DoesNotExist:
            return False