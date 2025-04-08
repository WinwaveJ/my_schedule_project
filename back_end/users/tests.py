from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from .models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.utils import IntegrityError


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

    def test_user_registration_invalid_email(self):
        """测试无效邮箱注册"""
        url = reverse("register")
        data = {
            "username": "newuser",
            "email": "invalid-email",
            "password": "newpass123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_weak_password(self):
        """测试弱密码注册"""
        url = reverse("register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "123",  # 太短的密码
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_empty_fields(self):
        """测试空字段注册"""
        url = reverse("register")
        data = {
            "username": "",
            "email": "",
            "password": "",
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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Unable to log in with provided credentials", str(response.data))

    def test_user_login_empty_fields(self):
        """测试空字段登录"""
        url = reverse("login")
        data = {"username": "", "password": ""}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("用户名不能为空", str(response.data))
        self.assertIn("密码不能为空", str(response.data))

    def test_user_login_case_sensitive(self):
        """测试登录用户名大小写敏感"""
        # 创建一个新用户，用户名全部小写
        User.objects.create_user(
            username="lowercase",
            email="lowercase@example.com",
            password="testpass123"
        )

        # 尝试使用大写用户名登录
        url = reverse("login")
        data = {"username": "LOWERCASE", "password": "testpass123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Unable to log in with provided credentials", str(response.data))

    def test_get_user_profile(self):
        """测试获取用户信息"""
        self.client.force_authenticate(user=self.user)
        url = reverse("user-profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")
        self.assertEqual(response.data["email"], "testuser@example.com")

    def test_get_user_profile_unauthorized(self):
        """测试未授权获取用户信息"""
        url = reverse("user-profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_profile(self):
        """测试更新用户信息"""
        self.client.force_authenticate(user=self.user)
        url = reverse("user-profile")
        data = {"email": "updated@example.com"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "updated@example.com")

    def test_update_user_profile_invalid_email(self):
        """测试更新用户信息为无效邮箱"""
        self.client.force_authenticate(user=self.user)
        url = reverse("user-profile")
        data = {"email": "invalid-email"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_user_profile_duplicate_email(self):
        """测试更新用户信息为已存在的邮箱"""
        # 创建另一个用户
        User.objects.create_user(
            username="anotheruser",
            email="another@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        url = reverse("user-profile")
        data = {"email": "another@example.com"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password(self):
        """测试修改密码"""
        self.client.force_authenticate(user=self.user)
        url = reverse("change-password")
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
        url = reverse("change-password")
        data = {"old_password": "wrongpass", "new_password": "newpass123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_weak_new_password(self):
        """测试使用弱密码修改密码"""
        self.client.force_authenticate(user=self.user)
        url = reverse("change-password")
        data = {"old_password": "testpass123", "new_password": "123"}  # 太短的密码
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_same_as_old(self):
        """测试新密码与旧密码相同"""
        self.client.force_authenticate(user=self.user)
        url = reverse("change-password")
        data = {"old_password": "testpass123", "new_password": "testpass123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_profile_integration(self):
        """测试用户信息相关功能的集成测试"""
        # 1. 注册新用户
        register_url = reverse("register")
        register_data = {
            "username": "integrationuser",
            "email": "integration@example.com",
            "password": "testpass123"
        }
        register_response = self.client.post(register_url, register_data, format="json")
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        # 2. 登录
        login_url = reverse("login")
        login_data = {
            "username": "integrationuser",
            "password": "testpass123"
        }
        login_response = self.client.post(login_url, login_data, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        token = login_response.data["token"]

        # 3. 使用token获取用户信息
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        profile_url = reverse("user-profile")
        profile_response = self.client.get(profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data["username"], "integrationuser")

        # 4. 更新用户信息
        update_data = {"email": "updated_integration@example.com"}
        update_response = self.client.patch(profile_url, update_data, format="json")
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

        # 5. 修改密码
        password_url = reverse("change-password")
        password_data = {
            "old_password": "testpass123",
            "new_password": "newpass123"
        }
        password_response = self.client.post(password_url, password_data, format="json")
        self.assertEqual(password_response.status_code, status.HTTP_200_OK)

        # 6. 使用新密码登录
        self.client.credentials()  # 清除认证信息
        new_login_data = {
            "username": "integrationuser",
            "password": "newpass123"
        }
        new_login_response = self.client.post(login_url, new_login_data, format="json")
        self.assertEqual(new_login_response.status_code, status.HTTP_200_OK)

    def test_user_username_case_sensitivity(self):
        """测试用户名大小写敏感性"""
        # 创建第一个用户
        user1 = User.objects.create_user(
            username='TestUser',
            email='test1@example.com',
            password='testpass123'
        )
        
        # 尝试创建相同用户名的用户（完全相同的大小写）
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username='TestUser',
                email='test2@example.com',
                password='testpass123'
            )
        
        # 验证可以创建不同大小写的用户名
        user2 = User.objects.create_user(
            username='TESTUSER',
            email='test2@example.com',
            password='testpass123'
        )
        
        # 验证两个用户都存在
        self.assertEqual(User.objects.filter(username__in=['TestUser', 'TESTUSER']).count(), 2)
        
        # 验证精确匹配查询
        self.assertEqual(User.objects.get(username__exact='TestUser'), user1)
        self.assertEqual(User.objects.get(username__exact='TESTUSER'), user2)

    def test_user_email_normalization(self):
        """测试邮箱地址标准化"""
        # 创建用户并验证邮箱被标准化为小写
        user = User.objects.create_user(
            username='testuser3',
            email='Test2@Example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test2@example.com')
        
        # 验证不能使用相同邮箱（即使大小写不同）创建新用户
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='testuser4',
                email='TEST2@EXAMPLE.COM',
                password='testpass123'
            )

    def test_user_role_validation(self):
        """测试用户角色验证"""
        # 测试有效角色
        user = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.assertEqual(user.role, 'user')
        
        # 测试无效角色
        with self.assertRaises(ValidationError):
            user.role = 'invalid_role'
            user.full_clean()

    def test_user_timestamps(self):
        """测试用户时间戳"""
        # 创建用户
        user = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='testpass123'
        )
        
        # 验证创建时间
        self.assertIsNotNone(user.created_at)
        self.assertLessEqual(user.created_at, timezone.now())
        
        # 验证最后登录时间
        self.assertIsNotNone(user.last_login)
        self.assertLessEqual(user.last_login, timezone.now())
        
        # 更新最后登录时间
        new_login_time = timezone.now() + timezone.timedelta(hours=1)
        user.last_login = new_login_time
        user.save()
        
        # 验证更新后的最后登录时间
        updated_user = User.objects.get(username='testuser3')
        self.assertEqual(updated_user.last_login, new_login_time)

    def test_user_permissions(self):
        """测试用户权限"""
        # 创建普通用户
        user = User.objects.create_user(
            username='testuser4',
            email='test4@example.com',
            password='testpass123'
        )
        
        # 创建管理员用户
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # 验证权限方法
        self.assertTrue(user.has_perm('any_perm'))
        self.assertTrue(user.has_module_perms('any_app'))
        self.assertTrue(admin.has_perm('any_perm'))
        self.assertTrue(admin.has_module_perms('any_app'))

    def test_user_string_representation(self):
        """测试用户字符串表示"""
        user = User.objects.create_user(
            username='testuser5',
            email='test5@example.com',
            password='testpass123'
        )
        self.assertEqual(str(user), 'testuser5')

    def test_user_id_property(self):
        """测试用户ID属性"""
        user = User.objects.create_user(
            username='testuser6',
            email='test6@example.com',
            password='testpass123'
        )
        self.assertEqual(user.id, user.user_id)
