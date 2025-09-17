from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from django.conf import settings


class JWTCookieAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads token from HTTP-only cookies.
    """
    
    def authenticate(self, request):
        # Get access token from cookie
        raw_token = request.COOKIES.get('access_token')
        
        if raw_token is None:
            return None
        
        # Validate token
        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        
        return (user, validated_token)
    
    def get_validated_token(self, raw_token):
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        messages = []
        for AuthToken in self.get_token_types():
            try:
                return AuthToken(raw_token)
            except TokenError as e:
                messages.append({
                    'token_class': AuthToken.__name__,
                    'token_type': AuthToken.token_type,
                    'message': e.args[0],
                })

        raise InvalidToken({
            'detail': 'Given token not valid for any token type',
            'messages': messages,
        })