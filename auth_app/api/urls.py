from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('activate/<str:uidb64>/<str:token>/', views.activate_account, name='activate_account'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', views.token_refresh_view, name='token_refresh'),
    path('password_reset/', views.password_reset_view, name='password_reset'),
    path('password_confirm/<str:uidb64>/<str:token>/', views.password_confirm_view, name='password_confirm'),
]
