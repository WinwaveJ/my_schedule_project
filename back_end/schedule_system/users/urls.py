# users/urls.py
from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserUpdateView,
    ChangePasswordView,
    UserLogoutView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("profile/", UserUpdateView.as_view(), name="user-profile"),
    path("password/", ChangePasswordView.as_view(), name="change-password"),
]
