# users/urls.py
from django.urls import path
from .views import UserRegistrationView, user_login, user_update, change_password, user_logout

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),
    path("profile/", user_update, name="user-profile"),
    path("password/", change_password, name="change-password"),
]
