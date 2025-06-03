"""
Custom permission classes for #FahanieCares role-based access control.
"""

from django.contrib.auth.models import Group, Permission
from django.core.cache import cache
from rest_framework.permissions import BasePermission
from guardian.shortcuts import get_objects_for_user
from functools import wraps
import hashlib


def cache_permission_check(timeout=300):
    """
    Decorator to cache permission check results.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, view, obj=None):
            # Create cache key based on user, view, and object
            user_id = request.user.id if request.user.is_authenticated else 'anonymous'
            view_name = view.__class__.__name__
            obj_id = obj.id if obj and hasattr(obj, 'id') else 'none'
            
            cache_key = f"perm_{user_id}_{view_name}_{obj_id}_{func.__name__}"
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Try to get from cache
            result = cache.get(cache_key, using='permissions')
            if result is not None:
                return result
            
            # Calculate permission
            result = func(self, request, view, obj)
            
            # Cache the result
            cache.set(cache_key, result, timeout, using='permissions')
            return result
        return wrapper
    return decorator


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    @cache_permission_check()
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return request.user.is_authenticated
        
        # Write permissions only to owner
        return obj.owner == request.user if hasattr(obj, 'owner') else False


class HasRolePermission(BasePermission):
    """
    Permission class that checks if user has required role for the action.
    """
    
    ROLE_HIERARCHY = {
        'constituent': 1,
        'member': 2,
        'chapter_member': 3,
        'coordinator': 4,
        'staff': 5,
        'mp': 6,
    }
    
    @cache_permission_check()
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Get required role from view
        required_role = getattr(view, 'required_role', None)
        if not required_role:
            return True
        
        user_role_level = self.ROLE_HIERARCHY.get(request.user.user_type, 0)
        required_role_level = self.ROLE_HIERARCHY.get(required_role, 6)
        
        return user_role_level >= required_role_level
    
    @cache_permission_check()
    def has_object_permission(self, request, view, obj):
        # First check general permission
        if not self.has_permission(request, view):
            return False
        
        # Check object-specific permissions if needed
        object_role = getattr(view, 'object_required_role', None)
        if object_role:
            user_role_level = self.ROLE_HIERARCHY.get(request.user.user_type, 0)
            object_role_level = self.ROLE_HIERARCHY.get(object_role, 6)
            return user_role_level >= object_role_level
        
        return True


class HasFeatureAccess(BasePermission):
    """
    Permission class that checks if user has access to specific features.
    """
    
    FEATURE_PERMISSIONS = {
        'referral_management': ['staff', 'mp'],
        'program_administration': ['coordinator', 'staff', 'mp'],
        'chapter_management': ['coordinator', 'staff', 'mp'],
        'analytics_view': ['coordinator', 'staff', 'mp'],
        'system_administration': ['mp'],
        'user_management': ['staff', 'mp'],
        'document_approval': ['staff', 'mp'],
        'notification_broadcast': ['coordinator', 'staff', 'mp'],
    }
    
    @cache_permission_check()
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Get required feature from view
        required_feature = getattr(view, 'required_feature', None)
        if not required_feature:
            return True
        
        allowed_roles = self.FEATURE_PERMISSIONS.get(required_feature, [])
        return request.user.user_type in allowed_roles
    
    @cache_permission_check()
    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class ChapterPermission(BasePermission):
    """
    Permission class for chapter-based access control.
    """
    
    @cache_permission_check()
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Staff and MP have access to all chapters
        if request.user.is_staff_or_above():
            return True
        
        # Chapter members can only access their own chapter
        return bool(request.user.chapter_id)
    
    @cache_permission_check()
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        # Staff and MP have access to all chapters
        if request.user.is_staff_or_above():
            return True
        
        # Check if object belongs to user's chapter
        if hasattr(obj, 'chapter_id'):
            return obj.chapter_id == request.user.chapter_id
        elif hasattr(obj, 'chapter'):
            return str(obj.chapter.id) == request.user.chapter_id
        
        return False


class RoleBasedMixin:
    """
    Mixin for views to easily implement role-based permissions.
    """
    
    def get_required_role(self):
        """Override this method to set required role dynamically."""
        return getattr(self, 'required_role', None)
    
    def get_required_feature(self):
        """Override this method to set required feature dynamically."""
        return getattr(self, 'required_feature', None)
    
    def check_permissions(self, request):
        """Check all permission requirements."""
        # Check role permission
        required_role = self.get_required_role()
        if required_role:
            permission = HasRolePermission()
            if not permission.has_permission(request, self):
                self.permission_denied(
                    request,
                    message=f"Role '{required_role}' or higher required."
                )
        
        # Check feature permission
        required_feature = self.get_required_feature()
        if required_feature:
            permission = HasFeatureAccess()
            if not permission.has_permission(request, self):
                self.permission_denied(
                    request,
                    message=f"Access to '{required_feature}' feature required."
                )


def setup_role_groups():
    """
    Set up Django Groups for role hierarchy with appropriate permissions.
    """
    
    # Define roles and their permissions
    role_permissions = {
        'Member': [
            'view_referral',
            'add_referral',
            'change_own_referral',
            'view_program',
            'view_chapter',
        ],
        'Chapter Member': [
            'view_referral',
            'add_referral',
            'change_own_referral',
            'view_program',
            'view_chapter',
            'add_constituent',
            'view_constituent',
        ],
        'Chapter Coordinator': [
            'view_referral',
            'add_referral',
            'change_referral',
            'view_program',
            'view_chapter',
            'change_chapter',
            'add_constituent',
            'change_constituent',
            'view_constituent',
            'add_user',
            'view_user',
        ],
        'Referral Staff': [
            'view_referral',
            'add_referral',
            'change_referral',
            'delete_referral',
            'view_program',
            'view_chapter',
            'view_constituent',
            'change_constituent',
            'view_user',
            'view_document',
            'add_document',
            'change_document',
        ],
        'Program Admin': [
            'view_program',
            'add_program',
            'change_program',
            'delete_program',
            'view_referral',
            'change_referral',
            'view_chapter',
            'change_chapter',
            'view_constituent',
            'change_constituent',
            'view_user',
            'change_user',
        ],
        'Superadmin': [
            # All permissions - will be granted via is_superuser
        ],
    }
    
    # Create groups and assign permissions
    for role_name, permission_names in role_permissions.items():
        group, created = Group.objects.get_or_create(name=role_name)
        
        if created or not group.permissions.exists():
            # Clear existing permissions
            group.permissions.clear()
            
            # Add permissions
            for perm_name in permission_names:
                try:
                    permission = Permission.objects.get(codename=perm_name)
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    print(f"Permission '{perm_name}' not found for group '{role_name}'")
        
        print(f"{'Created' if created else 'Updated'} group: {role_name}")


def assign_user_to_role_group(user):
    """
    Assign user to appropriate group based on user_type.
    """
    # Map user types to group names
    type_to_group = {
        'member': 'Member',
        'chapter_member': 'Chapter Member',
        'coordinator': 'Chapter Coordinator',
        'staff': 'Referral Staff',
        'mp': 'Superadmin',
    }
    
    # Remove user from all role groups first
    role_groups = Group.objects.filter(
        name__in=type_to_group.values()
    )
    user.groups.remove(*role_groups)
    
    # Add user to appropriate group
    group_name = type_to_group.get(user.user_type)
    if group_name:
        try:
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
        except Group.DoesNotExist:
            print(f"Group '{group_name}' not found")


def clear_permission_cache(user_id=None):
    """
    Clear permission cache for a specific user or all users.
    """
    if user_id:
        # Clear cache for specific user
        cache_pattern = f"perm_{user_id}_*"
    else:
        # Clear all permission cache
        cache_pattern = "perm_*"
    
    # Note: This is a simplified approach
    # In production, you might want to use Redis SCAN for better performance
    cache.clear(using='permissions')