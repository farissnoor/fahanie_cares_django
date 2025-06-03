"""
Mobile detection context processor for #FahanieCares.
"""

import re
from django.http import HttpRequest

MOBILE_AGENT_RE = re.compile(r".*(iphone|mobile|androidtouch)", re.IGNORECASE)

def is_mobile(request: HttpRequest) -> dict:
    """
    Detect if the user is on a mobile device.
    
    Args:
        request: The Django HTTP request object
        
    Returns:
        A dictionary containing mobile detection status
    """
    # Check user agent
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    is_mobile_agent = bool(MOBILE_AGENT_RE.match(user_agent))
    
    # Check if user forced mobile view
    force_mobile = request.session.get('force_mobile', False)
    
    # Check if user forced desktop view
    force_desktop = request.session.get('force_desktop', False)
    
    # Determine final mobile status
    mobile = (is_mobile_agent or force_mobile) and not force_desktop
    
    return {
        'is_mobile': mobile,
        'is_mobile_agent': is_mobile_agent,
        'force_mobile': force_mobile,
        'force_desktop': force_desktop,
    }