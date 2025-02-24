# users/urls.py
from django.urls import path
from .views import UserRegistrationView, user_login, user_update, change_password

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", user_login, name="login"),
    path("<int:user_id>/", user_update, name="user-update"),
    path("<int:user_id>/password/", change_password, name="change-password"),
]
