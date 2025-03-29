from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from .models import User


class UserTests(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="testpass123"
        )
        self.client = APIClient()

    def test_user_registration(self):
        """测试用户注册"""
        url = reverse("register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpass123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)  # 包括 setUp 中创建的用户
        self.assertEqual(response.data["username"], "newuser")
        self.assertEqual(response.data["email"], "newuser@example.com")

    def test_user_registration_duplicate_username(self):
        """测试重复用户名注册"""
        url = reverse("register")
        data = {
            "username": "testuser",  # 使用已存在的用户名
            "email": "another@example.com",
            "password": "newpass123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login(self):
        """测试用户登录"""
        url = reverse("login")
        data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "testuser")

    def test_user_login_invalid_credentials(self):
        """测试无效凭据登录"""
        url = reverse("login")
        data = {"username": "testuser", "password": "wrongpass"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_profile(self):
        """测试获取用户信息"""
        self.client.force_authenticate(user=self.user)
        url = reverse("user-update", args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")
        self.assertEqual(response.data["email"], "testuser@example.com")

    def test_get_user_profile_unauthorized(self):
        """测试未授权获取用户信息"""
        url = reverse("user-update", args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_profile(self):
        """测试更新用户信息"""
        self.client.force_authenticate(user=self.user)
        url = reverse("user-update", args=[self.user.id])
        data = {"email": "updated@example.com"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "updated@example.com")

    def test_change_password(self):
        """测试修改密码"""
        self.client.force_authenticate(user=self.user)
        url = reverse("change-password", args=[self.user.id])
        data = {"old_password": "testpass123", "new_password": "newpass123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证新密码是否生效
        self.client.logout()
        login_url = reverse("login")
        login_data = {"username": "testuser", "password": "newpass123"}
        login_response = self.client.post(login_url, login_data, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_change_password_invalid_old_password(self):
        """测试使用错误的旧密码修改密码"""
        self.client.force_authenticate(user=self.user)
        url = reverse("change-password", args=[self.user.id])
        data = {"old_password": "wrongpass", "new_password": "newpass123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
