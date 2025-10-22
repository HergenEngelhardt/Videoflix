from django.urls import path
from . import auth_views, activation_views, password_views

urlpatterns = [
    # Authentication endpoints
    path('register/', auth_views.RegistrationView.as_view(), name='register'),
    path('login/', auth_views.login_user, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Account activation endpoints
    path('activate/<str:uidb64>/<str:token>/', activation_views.activate_account, name='activate_account'),
    path('activate-redirect/<str:uidb64>/<str:token>/', activation_views.activate_redirect, name='activate_redirect'),
    
    # Password reset endpoints
    path('password_reset/', password_views.password_reset_view, name='password_reset'),
    path('password-reset-redirect/<str:uidb64>/<str:token>/', password_views.password_reset_redirect, name='password_reset_redirect'),
    path('password_reset_confirm/<str:uidb64>/<str:token>/', password_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password_confirm/<str:uidb64>/<str:token>/', password_views.password_confirm_view, name='password_confirm'),
    
    # Token management endpoints
    path('token/refresh/', password_views.token_refresh_view, name='token_refresh'),
]
