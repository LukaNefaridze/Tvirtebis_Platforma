from rest_framework import authentication
from rest_framework import exceptions
from django.utils.translation import gettext_lazy as _
from apps.bids.models import PlatformAPIKey


class PlatformAPIKeyAuthentication(authentication.BaseAuthentication):
    """
    API Key authentication for platform access.
    Expects header: Authorization: Bearer {api_key}
    """
    
    keyword = 'Bearer'
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (platform, api_key).
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None
        
        # Parse the header
        parts = auth_header.split()
        
        if len(parts) == 0:
            return None
        
        if parts[0].lower() != self.keyword.lower():
            return None
        
        if len(parts) == 1:
            raise exceptions.AuthenticationFailed(_('Invalid token header. No credentials provided.'))
        elif len(parts) > 2:
            raise exceptions.AuthenticationFailed(_('Invalid token header. Token string should not contain spaces.'))
        
        raw_key = parts[1]
        
        return self.authenticate_credentials(raw_key)
    
    def authenticate_credentials(self, raw_key):
        """
        Authenticate the API key and return (platform, api_key).
        """
        # Try to find matching API key by checking all active keys
        api_keys = PlatformAPIKey.objects.filter(is_active=True).select_related('platform')
        
        for api_key in api_keys:
            if api_key.check_key(raw_key):
                # Check if platform is active
                if not api_key.platform.is_active:
                    raise exceptions.AuthenticationFailed(_('Platform account is inactive.'))
                
                # Update last used timestamp
                api_key.mark_used()
                
                # Return platform as user and api_key as auth
                return (api_key.platform, api_key)
        
        # No matching key found
        raise exceptions.AuthenticationFailed(_('Invalid API key.'))
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the WWW-Authenticate
        header in a 401 Unauthenticated response.
        """
        return self.keyword
