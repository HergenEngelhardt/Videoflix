from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class JWTCookieAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads token from HTTP-only cookies.
    """

    def authenticate(self, request):
        """Authenticate user from HTTP-only cookie token."""
        raw_token = request.COOKIES.get('access_token')

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)

        return (user, validated_token)

    def collect_token_validation_messages(self, raw_token):
        """Collect validation messages from all token types."""
        from rest_framework_simplejwt.tokens import AccessToken
        messages = []
        try:
            return AccessToken(raw_token), None
        except TokenError as e:
            messages.append({
                'token_class': AccessToken.__name__,
                'token_type': AccessToken.token_type,
                'message': e.args[0],
            })
        return None, messages

    def get_validated_token(self, raw_token):
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        token, messages = self.collect_token_validation_messages(raw_token)
        if token:
            return token

        raise InvalidToken({
            'detail': 'Given token not valid for any token type',
            'messages': messages,
        })
