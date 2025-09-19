from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom User Model extending Django's AbstractUser.
    Uses email as unique identifier instead of username.
    """
    email = models.EmailField(unique=True, verbose_name="Email Address")
    is_active = models.BooleanField(default=False, verbose_name="Active")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Date Joined")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
