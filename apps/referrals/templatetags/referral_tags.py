"""
Custom template tags and filters for the referrals app.
"""

from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key."""
    return dictionary.get(key, 0)

@register.filter
def subtract(value, arg):
    """Subtract the arg from the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percent_of_max(value, queryset):
    """Calculate the percentage of value to the max value in a queryset."""
    try:
        # Find the maximum value - use the first item's referral_count as this should be sorted
        max_value = queryset[0].get('referral_count', 0)
        if max_value == 0:
            return 0
        
        # Calculate percentage
        return (float(value) / float(max_value)) * 100
    except (ValueError, TypeError, IndexError, AttributeError):
        return 0