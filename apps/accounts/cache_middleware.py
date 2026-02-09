"""
Middleware to prevent browser caching of authenticated pages.
This ensures users always see fresh content after login/logout.
"""
from django.utils.cache import add_never_cache_headers


class NoCacheForAuthenticatedMiddleware:
    """
    Add no-cache headers to all responses for authenticated users.
    This prevents the browser from caching pages that contain user-specific data.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add no-cache headers for authenticated users
        if hasattr(request, 'user') and request.user.is_authenticated:
            add_never_cache_headers(response)
            # Additional cache control headers
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response
