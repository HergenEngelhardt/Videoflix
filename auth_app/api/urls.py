from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import auth_views, activation_views, password_views

urlpatterns = [
    path('register/', auth_views.RegistrationView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('activate/<str:uidb64>/<str:token>/', activation_views.activate_account, name='activate_account'),
    path('activate-redirect/<str:uidb64>/<str:token>/', activation_views.activate_redirect, name='activate_redirect'),
    path('password_reset/', password_views.password_reset_view, name='password_reset'),
    path('password-reset-redirect/<str:uidb64>/<str:token>/', password_views.password_reset_redirect, name='password_reset_redirect'),
    path('password_confirm/<str:uidb64>/<str:token>/', password_views.PasswordResetConfirmView.as_view(), name='password_confirm'),
    path('token/refresh/', password_views.CookieRefreshView.as_view(), name='token_refresh'),
]
