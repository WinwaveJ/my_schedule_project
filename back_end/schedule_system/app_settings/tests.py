from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import AppSettings
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class AppSettingsTests(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.user1 = User.objects.create_user(
            username="testuser1", email="testuser1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", email="testuser2@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user1)

        # 创建用户1的设置
        self.settings1 = AppSettings.objects.create(
            user=self.user1,
            pomodoro_duration=25,
            short_break_duration=5,
            long_break_duration=15,
            long_break_interval=4,
            daily_pomodoro_goal=8,
            daily_stopwatch_goal=7200,
        )

    def test_settings_creation(self):
        """测试设置创建"""
        self.client.force_authenticate(user=self.user2)
        url = reverse("appsettings-list")
        data = {
            "pomodoro_duration": 25,
            "short_break_duration": 5,
            "long_break_duration": 15,
            "long_break_interval": 4,
            "daily_pomodoro_goal": 8,
            "daily_stopwatch_goal": 7200,
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AppSettings.objects.count(), 2)

    def test_settings_retrieval(self):
        """测试设置获取"""
        url = reverse("appsettings-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pomodoro_duration"], 25)

    def test_settings_update(self):
        """测试设置更新"""
        url = reverse("appsettings-detail", args=[self.settings1.id])
        data = {
            "pomodoro_duration": 30,
            "short_break_duration": 10,
            "long_break_duration": 20,
            "long_break_interval": 5,
            "daily_pomodoro_goal": 10,
            "daily_stopwatch_goal": 180,
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证更新结果
        self.settings1.refresh_from_db()
        self.assertEqual(self.settings1.pomodoro_duration, 30)
        self.assertEqual(self.settings1.short_break_duration, 10)
        self.assertEqual(self.settings1.long_break_duration, 20)
        self.assertEqual(self.settings1.long_break_interval, 5)
        self.assertEqual(self.settings1.daily_pomodoro_goal, 10)
        self.assertEqual(self.settings1.daily_stopwatch_goal, 180)

    def test_settings_validation(self):
        """测试设置验证"""
        url = reverse("appsettings-detail", args=[self.settings1.id])
        # 测试无效的番茄钟时长
        data = {"pomodoro_duration": 0}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 测试无效的休息时长
        data = {"short_break_duration": -1}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 测试无效的长休息间隔
        data = {"long_break_interval": 0}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_settings_user_isolation(self):
        """测试应用设置用户隔离"""
        # 删除已存在的设置
        AppSettings.objects.filter(user=self.user1).delete()

        # 创建另一个用户
        other_user = User.objects.create_user(
            username="other_user", email="other@example.com", password="testpass123"
        )

        # 为当前用户创建设置
        settings = AppSettings.objects.create(
            user=self.user1,
            pomodoro_duration=25,
            short_break_duration=5,
            long_break_duration=15,
            long_break_interval=4,
            daily_pomodoro_goal=8,
            daily_stopwatch_goal=7200,
        )

        # 为其他用户创建设置
        other_settings = AppSettings.objects.create(
            user=other_user,
            pomodoro_duration=30,
            short_break_duration=10,
            long_break_duration=20,
            long_break_interval=5,
            daily_pomodoro_goal=10,
            daily_stopwatch_goal=3600,
        )

        # 验证设置是否正确隔离
        self.assertEqual(settings.user, self.user1)
        self.assertEqual(other_settings.user, other_user)
        self.assertNotEqual(
            settings.pomodoro_duration, other_settings.pomodoro_duration
        )

    def test_settings_default_values(self):
        """测试设置默认值"""
        # 删除已存在的设置
        AppSettings.objects.filter(user=self.user1).delete()

        # 创建用户设置
        settings = AppSettings.objects.create(user=self.user1)

        # 验证默认值
        self.assertEqual(settings.pomodoro_duration, 25)
        self.assertEqual(settings.short_break_duration, 5)
        self.assertEqual(settings.long_break_duration, 15)
        self.assertEqual(settings.long_break_interval, 4)
        self.assertEqual(settings.daily_pomodoro_goal, 8)
        self.assertEqual(settings.daily_stopwatch_goal, 120)  # 默认值为120分钟

    def test_settings_validation(self):
        """测试设置验证规则"""
        # 测试无效的番茄钟时长
        data = {
            "pomodoro_duration": 0,  # 无效值
            "short_break_duration": 5,
            "long_break_duration": 15,
            "long_break_interval": 4,
            "daily_pomodoro_goal": 8,
            "daily_stopwatch_goal": 7200,
        }

        response = self.client.put(
            reverse("appsettings-detail", args=[self.settings1.id]),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('pomodoro_duration', response.data)

        # 测试无效的休息时长
        data = {
            "pomodoro_duration": 25,
            "short_break_duration": -1,  # 无效值
            "long_break_duration": 15,
            "long_break_interval": 4,
            "daily_pomodoro_goal": 8,
            "daily_stopwatch_goal": 7200,
        }

        response = self.client.put(
            reverse("appsettings-detail", args=[self.settings1.id]),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('short_break_duration', response.data)

    def test_settings_update_partial(self):
        """测试部分更新设置"""
        # 只更新部分字段
        data = {
            "pomodoro_duration": 30,
            "short_break_duration": 10,
        }

        response = self.client.patch(
            reverse("appsettings-detail", args=[self.settings1.id]),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证更新后的值
        self.settings1.refresh_from_db()
        self.assertEqual(self.settings1.pomodoro_duration, 30)
        self.assertEqual(self.settings1.short_break_duration, 10)

        # 验证其他字段保持不变
        self.assertEqual(self.settings1.long_break_duration, 15)
        self.assertEqual(self.settings1.long_break_interval, 4)
        self.assertEqual(self.settings1.daily_pomodoro_goal, 8)
        self.assertEqual(self.settings1.daily_stopwatch_goal, 7200)

    def test_duplicate_settings_creation(self):
        """测试重复创建设置"""
        url = reverse("appsettings-list")
        data = {
            "pomodoro_duration": 25,
            "short_break_duration": 5,
            "long_break_duration": 15,
            "long_break_interval": 4,
            "daily_pomodoro_goal": 8,
            "daily_stopwatch_goal": 7200,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], '用户设置已存在，请使用更新接口')

    def test_unauthorized_settings_access(self):
        """测试未授权访问设置"""
        self.client.force_authenticate(user=None)
        
        # 测试获取设置列表
        response = self.client.get(reverse("appsettings-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 测试获取单个设置
        response = self.client.get(reverse("appsettings-detail", args=[self.settings1.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 测试创建设置
        data = {
            "pomodoro_duration": 25,
            "short_break_duration": 5,
            "long_break_duration": 15,
            "long_break_interval": 4,
            "daily_pomodoro_goal": 8,
            "daily_stopwatch_goal": 7200,
        }
        response = self.client.post(reverse("appsettings-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_other_user_settings_access(self):
        """测试访问其他用户的设置"""
        # 创建另一个用户的设置
        other_settings = AppSettings.objects.create(
            user=self.user2,
            pomodoro_duration=30,
            short_break_duration=10,
            long_break_duration=20,
            long_break_interval=5,
            daily_pomodoro_goal=10,
            daily_stopwatch_goal=3600,
        )
        
        # 尝试访问其他用户的设置
        response = self.client.get(reverse("appsettings-detail", args=[other_settings.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
        self.assertEqual(str(response.data['detail']), '您没有权限访问其他用户的设置')
        
        # 尝试更新其他用户的设置
        data = {"pomodoro_duration": 35}
        response = self.client.patch(
            reverse("appsettings-detail", args=[other_settings.id]),
            data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
        self.assertEqual(str(response.data['detail']), '您没有权限访问其他用户的设置')
        
        # 尝试删除其他用户的设置
        response = self.client.delete(reverse("appsettings-detail", args=[other_settings.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_settings_values(self):
        """测试无效的设置值"""
        url = reverse("appsettings-detail", args=[self.settings1.id])
        
        # 测试番茄钟时长为负数
        data = {"pomodoro_duration": -5}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('pomodoro_duration', response.data)
        
        # 测试休息时长为零
        data = {"short_break_duration": 0}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('short_break_duration', response.data)
        
        # 测试长休息间隔为负数
        data = {"long_break_interval": -2}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('long_break_interval', response.data)
        
        # 测试每日目标为零
        data = {"daily_pomodoro_goal": 0}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('daily_pomodoro_goal', response.data)
