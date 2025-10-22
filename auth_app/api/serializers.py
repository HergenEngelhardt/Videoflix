import re
import uuid
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from ..models import CustomUser


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration.
    Validates email uniqueness, password strength, and confirmation matching."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'email': {
                'required': True
            },
        }

    def validate_confirmed_password(self, value):
        """Ensure the confirmed password matches the original password."""
        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError('Passwords do not match')
        return value

    def validate_email(self, value):
        """Validate that the email contains only ASCII characters and is unique."""
        if not re.match(r'^[\x00-\x7F]+$', value):
            raise serializers.ValidationError('Unicode characters in email are not allowed')

        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def save(self):
        """Create a new inactive user account with a unique username and hashed password."""
        pw = self.validated_data['password']
        email = self.validated_data['email']
        username = email.split('@')[0]

        if CustomUser.objects.filter(username=username).exists():
            username = f"{username}_{uuid.uuid4().hex[:8]}"

        account = CustomUser(email=email, username=username, is_active=False)
        account.set_password(pw)
        account.save()
        return account


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer authenticating users via email and password instead of username."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "username" in self.fields:
            self.fields.pop("username")

    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['confirmed_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs

    def create(self, validated_data):
        """Create new user with encrypted password."""
        validated_data.pop('confirmed_password')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login.
    Authenticates credentials and validates account activation status."""
    email = serializers.EmailField()
    password = serializers.CharField()

    def authenticate_user_credentials(self, email, password):
        """Authenticate user with email and password."""
        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError('Invalid credentials.')
        if not user.is_active:
            raise serializers.ValidationError('Account is not activated.')
        return user

    def validate(self, attrs):
        """Validate user credentials."""
        email = attrs.get('email')
        password = attrs.get('password')

        if isinstance(email, str):
            email = email.lower()
            attrs['email'] = email

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")

        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password")

        attrs['username'] = user.username
        data = super().validate(attrs)

        return data


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for initiating a password reset request via email."""
    email = serializers.EmailField()

    def validate_email(self, value):
        """Normalize the email address by lowercasing and trimming whitespace."""
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming and setting a new user password."""
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Das neue Passwort (mindestens 8 Zeichen)"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        help_text="Bestätigung des neuen Passworts"
    )

    def validate_new_password(self, value):
        """Validate the new password against Django's standard password policies."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate(self, attrs):
        """Ensure the new password and confirmation password match."""
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError("Passwords do not match")

        return attrs

    def save(self, user):
        """Set the new password for the user."""
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user





class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data."""
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'date_joined')
        read_only_fields = ('id', 'date_joined')
