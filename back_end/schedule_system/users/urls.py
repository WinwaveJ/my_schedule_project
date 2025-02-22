# users/urls.py
from django.urls import path
from .views import UserRegistrationView, user_login

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", user_login, name="login"),
]
