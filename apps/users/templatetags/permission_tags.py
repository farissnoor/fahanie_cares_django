"""
Template tags for permission checking in #FahanieCares.
"""

from django import template
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from guardian.shortcuts import get_perms
import hashlib

register = template.Library()


@register.simple_tag
def has_permission(user, permission, obj=None):
    """
    Check if user has a specific permission on an object.
    
    Usage: {% has_permission user 'change_referral' referral_obj %}
    """
    if isinstance(user, AnonymousUser):
        return False
    
    # Create cache key
    obj_id = obj.id if obj and hasattr(obj, 'id') else 'none'
    cache_key = f"template_perm_{user.id}_{permission}_{obj_id}"
    cache_key = hashlib.md5(cache_key.encode()).hexdigest()
    
    # Try cache first
    result = cache.get(cache_key, using='permissions')
    if result is not None:
        return result
    
    # Check permission
    if obj:
        # Object-level permission
        result = user.has_perm(permission, obj)
    else:
        # Model-level permission
        result = user.has_perm(permission)
    
    # Cache result
    cache.set(cache_key, result, 300, using='permissions')
    return result


@register.simple_tag
def has_role(user, role):
    """
    Check if user has a specific role.
    
    Usage: {% has_role user 'staff' %}
    """
    if isinstance(user, AnonymousUser):
        return False
    
    return getattr(user, 'user_type', None) == role


@register.simple_tag
def has_role_or_higher(user, role):
    """
    Check if user has a specific role or higher.
    
    Usage: {% has_role_or_higher user 'coordinator' %}
    """
    if isinstance(user, AnonymousUser):
        return False
    
    from ..permissions import HasRolePermission
    
    user_level = HasRolePermission.ROLE_HIERARCHY.get(getattr(user, 'user_type', ''), 0)
    required_level = HasRolePermission.ROLE_HIERARCHY.get(role, 0)
    
    return user_level >= required_level


@register.simple_tag
def has_feature_access(user, feature):
    """
    Check if user has access to a specific feature.
    
    Usage: {% has_feature_access user 'referral_management' %}
    """
    if isinstance(user, AnonymousUser):
        return False
    
    from ..permissions import HasFeatureAccess
    
    permission = HasFeatureAccess()
    allowed_roles = permission.FEATURE_PERMISSIONS.get(feature, [])
    user_role = getattr(user, 'user_type', '')
    
    return user_role in allowed_roles


@register.simple_tag
def can_manage_chapter(user, chapter=None):
    """
    Check if user can manage a specific chapter.
    
    Usage: {% can_manage_chapter user chapter_obj %}
    """
    if isinstance(user, AnonymousUser):
        return False
    
    # Staff and MP can manage all chapters
    if hasattr(user, 'is_staff_or_above') and user.is_staff_or_above():
        return True
    
    # Coordinators can manage their own chapter
    if getattr(user, 'user_type', '') == 'coordinator':
        if chapter:
            return str(chapter.id) == getattr(user, 'chapter_id', '')
        return bool(getattr(user, 'chapter_id', ''))
    
    return False


@register.simple_tag
def can_view_referral(user, referral):
    """
    Check if user can view a specific referral.
    
    Usage: {% can_view_referral user referral_obj %}
    """
    if isinstance(user, AnonymousUser):
        return False
    
    # Staff and MP can view all referrals
    if hasattr(user, 'is_staff_or_above') and user.is_staff_or_above():
        return True
    
    # Users can view their own referrals
    if hasattr(referral, 'owner') and referral.owner == user:
        return True
    
    # Chapter coordinators can view referrals from their chapter
    if (getattr(user, 'user_type', '') == 'coordinator' and 
        hasattr(referral, 'chapter_id') and 
        referral.chapter_id == getattr(user, 'chapter_id', '')):
        return True
    
    return False


@register.simple_tag
def can_edit_referral(user, referral):
    """
    Check if user can edit a specific referral.
    
    Usage: {% can_edit_referral user referral_obj %}
    """
    if isinstance(user, AnonymousUser):
        return False
    
    # Staff and MP can edit all referrals
    if hasattr(user, 'is_staff_or_above') and user.is_staff_or_above():
        return True
    
    # Users can edit their own pending referrals
    if (hasattr(referral, 'owner') and referral.owner == user and 
        getattr(referral, 'status', '') in ['pending', 'submitted']):
        return True
    
    return False


@register.filter
def user_role_display(user):
    """
    Get a human-readable display of the user's role.
    
    Usage: {{ user|user_role_display }}
    """
    if isinstance(user, AnonymousUser):
        return 'Guest'
    
    role_map = {
        'constituent': 'Constituent',
        'member': 'Member',
        'chapter_member': 'Chapter Member',
        'coordinator': 'Chapter Coordinator',
        'staff': 'Parliamentary Staff',
        'mp': 'Member of Parliament',
    }
    
    return role_map.get(getattr(user, 'user_type', ''), 'Unknown')


@register.inclusion_tag('components/navigation/role_menu.html', takes_context=True)
def role_navigation_menu(context):
    """
    Render role-based navigation menu.
    
    Usage: {% role_navigation_menu %}
    """
    request = context['request']
    user = request.user
    
    if isinstance(user, AnonymousUser):
        return {'nav_items': []}
    
    # Get navigation items from middleware
    nav_items = getattr(request, 'navigation_items', [])
    
    return {
        'nav_items': nav_items,
        'user': user,
        'user_role': getattr(user, 'user_type', ''),
        'request': request,
    }


@register.inclusion_tag('components/permissions/feature_check.html')
def feature_access_check(user, feature, show_message=True):
    """
    Check feature access and optionally show a message.
    
    Usage: {% feature_access_check user 'referral_management' %}
    """
    has_access = has_feature_access(user, feature)
    
    return {
        'has_access': has_access,
        'feature': feature,
        'user': user,
        'show_message': show_message,
    }


@register.simple_tag(takes_context=True)
def available_features(context):
    """
    Get list of features available to the current user.
    
    Usage: {% available_features as features %}
    """
    request = context['request']
    return getattr(request, 'available_features', [])


@register.simple_tag
def user_permissions(user):
    """
    Get list of permissions for the user.
    
    Usage: {% user_permissions user as permissions %}
    """
    if isinstance(user, AnonymousUser):
        return []
    
    # Get from cache
    cache_key = f"user_perms_{user.id}"
    permissions = cache.get(cache_key, using='permissions')
    
    if permissions is None:
        permissions = []
        
        # Get permissions from groups
        for group in user.groups.all():
            permissions.extend([
                perm.codename for perm in group.permissions.all()
            ])
        
        # Get direct permissions
        permissions.extend([
            perm.codename for perm in user.user_permissions.all()
        ])
        
        permissions = list(set(permissions))
        cache.set(cache_key, permissions, 300, using='permissions')
    
    return permissions


@register.simple_tag
def chapter_members_count(chapter):
    """
    Get count of members in a chapter.
    
    Usage: {% chapter_members_count chapter_obj %}
    """
    if not chapter:
        return 0
    
    cache_key = f"chapter_members_{chapter.id}"
    count = cache.get(cache_key)
    
    if count is None:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        count = User.objects.filter(chapter_id=str(chapter.id)).count()
        cache.set(cache_key, count, 600)  # Cache for 10 minutes
    
    return count


@register.simple_tag
def pending_referrals_count(user):
    """
    Get count of pending referrals for a user or chapter.
    
    Usage: {% pending_referrals_count user %}
    """
    if isinstance(user, AnonymousUser):
        return 0
    
    cache_key = f"pending_referrals_{user.id}"
    count = cache.get(cache_key)
    
    if count is None:
        from ...referrals.models import Referral
        
        if hasattr(user, 'is_staff_or_above') and user.is_staff_or_above():
            # Staff can see all pending referrals
            count = Referral.objects.filter(status='pending').count()
        elif getattr(user, 'user_type', '') == 'coordinator':
            # Coordinators see pending referrals from their chapter
            count = Referral.objects.filter(
                status='pending',
                chapter_id=getattr(user, 'chapter_id', '')
            ).count()
        else:
            # Regular users see their own pending referrals
            count = Referral.objects.filter(
                status='pending',
                owner=user
            ).count()
        
        cache.set(cache_key, count, 300)  # Cache for 5 minutes
    
    return count