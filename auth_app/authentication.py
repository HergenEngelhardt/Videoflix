from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed


class JWTCookieAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads token from HTTP-only cookies.
    """

    def authenticate(self, request):
        """Authenticate user from HTTP-only cookie token."""
        raw_token = request.COOKIES.get('access_token')
        
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except (InvalidToken, TokenError, AuthenticationFailed):
            return None


