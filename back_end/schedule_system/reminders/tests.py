from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Reminder
from .serializers import ReminderSerializer
from datetime import timedelta
from django.core.exceptions import ValidationError
from tasks.models import Task
from activities.models import PomodoroActivity, StopwatchActivity
from django.urls import reverse

User = get_user_model()

class ReminderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.reminder = Reminder.objects.create(
            user=self.user,
            title='测试提醒',
            content='测试内容',
            reminder_type='CUSTOM',
            reminder_method='EMAIL',
            reminder_time=timezone.now() + timedelta(days=1)
        )
        self.task = Task.objects.create(
            user=self.user,
            title='测试任务',
            description='测试任务描述',
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1)
        )
        self.pomodoro_activity = PomodoroActivity.objects.create(
            title="Test Pomodoro",
            description="Test Description",
            user=self.user,
            task=self.task,
            status="PENDING",
        )
        self.stopwatch_activity = StopwatchActivity.objects.create(
            title="Test Stopwatch",
            description="Test Description",
            user=self.user,
            task=self.task,
            status="PENDING",
        )

    def test_reminder_creation(self):
        """测试提醒创建"""
        self.assertEqual(self.reminder.title, '测试提醒')
        self.assertEqual(self.reminder.content, '测试内容')
        self.assertEqual(self.reminder.reminder_type, 'CUSTOM')
        self.assertEqual(self.reminder.reminder_method, 'EMAIL')
        self.assertTrue(self.reminder.is_active)

    def test_reminder_str_representation(self):
        """测试提醒的字符串表示"""
        expected_str = f"{self.user.username} - 测试提醒"
        self.assertEqual(str(self.reminder), expected_str)

    def test_reminder_validation(self):
        """测试提醒验证"""
        # 测试提醒时间不能早于当前时间
        with self.assertRaises(ValidationError):
            reminder = Reminder(
                user=self.user,
                title='测试提醒',
                content='测试内容',
                reminder_type='CUSTOM',
                reminder_method='EMAIL',
                reminder_time=timezone.now() - timezone.timedelta(days=1)
            )
            reminder.full_clean()

        # 测试周期性提醒的验证
        with self.assertRaises(ValidationError):
            reminder = Reminder(
                user=self.user,
                title='测试周期性提醒',
                content='测试内容',
                reminder_type='PERIODIC',
                reminder_method='EMAIL',
                reminder_time=timezone.now() + timezone.timedelta(days=1),
                is_periodic=True,
                periodic_type='DAILY',
                periodic_interval=1,
                periodic_end_date=timezone.now()  # 结束时间早于提醒时间
            )
            reminder.full_clean()

        # 测试重复提醒的验证
        with self.assertRaises(ValidationError):
            reminder = Reminder(
                user=self.user,
                title='测试重复提醒',
                content='测试内容',
                reminder_type='CUSTOM',
                reminder_method='EMAIL',
                reminder_time=timezone.now() + timezone.timedelta(days=1),
                repeat_reminder=True,
                repeat_interval=30,
                max_repeats=None  # 缺少最大重复次数
            )
            reminder.full_clean()

        # 测试任务提醒必须关联任务
        with self.assertRaises(ValidationError):
            reminder = Reminder(
                title="无效的任务提醒",
                description="这是一个无效的任务提醒",
                user=self.user,
                reminder_type="TASK",
                remind_at=timezone.now() + timezone.timedelta(hours=1),
            )
            reminder.clean()

        # 测试活动提醒必须关联活动
        with self.assertRaises(ValidationError):
            reminder = Reminder(
                title="无效的活动提醒",
                description="这是一个无效的活动提醒",
                user=self.user,
                reminder_type="ACTIVITY",
                remind_at=timezone.now() + timezone.timedelta(hours=1),
            )
            reminder.clean()

    def test_periodic_reminder(self):
        """测试周期性提醒功能"""
        # 创建周期性提醒
        reminder = Reminder.objects.create(
            user=self.user,
            title='测试周期性提醒',
            content='测试内容',
            reminder_type='PERIODIC',
            reminder_method='EMAIL',
            reminder_time=timezone.now() + timezone.timedelta(days=1),
            is_periodic=True,
            periodic_type='DAILY',
            periodic_interval=1,
            periodic_end_date=timezone.now() + timezone.timedelta(days=7)
        )

        # 验证周期性提醒的属性
        self.assertTrue(reminder.is_periodic)
        self.assertEqual(reminder.periodic_type, 'DAILY')
        self.assertEqual(reminder.periodic_interval, 1)
        self.assertIsNotNone(reminder.periodic_end_date)

        # 测试无效的周期类型
        with self.assertRaises(ValidationError):
            reminder.periodic_type = 'INVALID'
            reminder.full_clean()

    def test_repeat_reminder(self):
        """测试重复提醒功能"""
        # 创建重复提醒
        reminder = Reminder.objects.create(
            user=self.user,
            title='测试重复提醒',
            content='测试内容',
            reminder_type='CUSTOM',
            reminder_method='EMAIL',
            reminder_time=timezone.now() + timezone.timedelta(days=1),
            repeat_reminder=True,
            repeat_interval=30,
            max_repeats=3
        )

        # 验证重复提醒的属性
        self.assertTrue(reminder.repeat_reminder)
        self.assertEqual(reminder.repeat_interval, 30)
        self.assertEqual(reminder.max_repeats, 3)
        self.assertEqual(reminder.current_repeats, 0)

        # 测试重复次数更新
        reminder.current_repeats += 1
        reminder.save()
        self.assertEqual(reminder.current_repeats, 1)

    def test_reminder_related_objects(self):
        """测试提醒与任务和活动的关联"""
        # 创建任务
        task = Task.objects.create(
            user=self.user,
            title='测试任务',
            description='测试描述',
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1)
        )
        
        # 创建活动
        activity = PomodoroActivity.objects.create(
            user=self.user,
            task=task,
            title='测试活动',
            description='测试描述',
            status="PENDING"
        )
        
        # 创建提醒
        reminder = Reminder.objects.create(
            user=self.user,
            title='测试提醒',
            content='测试内容',
            reminder_type='TASK_DUE',
            reminder_method='EMAIL',
            related_task=task,
            reminder_time=timezone.now() + timezone.timedelta(hours=1)
        )
        
        # 验证关联
        self.assertEqual(reminder.related_task, task)
        self.assertEqual(activity.task, task)
        self.assertEqual(task.reminders.count(), 1)
        self.assertEqual(task.pomodoro_activities.count(), 1)

    def test_reminder_ordering(self):
        """测试提醒排序"""
        # 删除已有的提醒
        Reminder.objects.all().delete()
        
        base_time = timezone.now()
        
        # 创建多个提醒
        reminder1 = Reminder.objects.create(
            user=self.user,
            title='Test Reminder 1',
            content='内容1',
            reminder_type='CUSTOM',
            reminder_method='EMAIL',
            reminder_time=base_time + timezone.timedelta(days=2)
        )

        reminder2 = Reminder.objects.create(
            user=self.user,
            title='Test Reminder 2',
            content='内容2',
            reminder_type='CUSTOM',
            reminder_method='EMAIL',
            reminder_time=base_time + timezone.timedelta(days=1)
        )

        reminder3 = Reminder.objects.create(
            user=self.user,
            title='Test Reminder 3',
            content='内容3',
            reminder_type='CUSTOM',
            reminder_method='EMAIL',
            reminder_time=base_time + timezone.timedelta(days=3)
        )

        # 验证按提醒时间正序排序
        reminders = Reminder.objects.all().order_by('reminder_time')
        self.assertEqual(reminders[0].title, 'Test Reminder 2')  # 最早
        self.assertEqual(reminders[1].title, 'Test Reminder 1')  # 中间
        self.assertEqual(reminders[2].title, 'Test Reminder 3')  # 最晚

    def test_bulk_delete(self):
        """测试批量删除提醒"""
        # 创建API客户端并认证
        client = APIClient()
        client.force_authenticate(user=self.user)
        
        # 删除所有提醒
        Reminder.objects.all().delete()
        
        # 创建两个提醒
        reminder1 = Reminder.objects.create(
            user=self.user,
            title='测试提醒1',
            content='内容1',
            reminder_type='CUSTOM',
            reminder_method='EMAIL',
            reminder_time=timezone.now() + timezone.timedelta(days=1)
        )
        
        reminder2 = Reminder.objects.create(
            user=self.user,
            title='测试提醒2',
            content='内容2',
            reminder_type='CUSTOM',
            reminder_method='EMAIL',
            reminder_time=timezone.now() + timezone.timedelta(days=2)
        )
        
        # 批量删除提醒
        data = {'reminder_ids': [reminder1.id, reminder2.id]}
        response = client.post('/api/reminders/bulk_delete/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Reminder.objects.filter(user=self.user).count(), 0)  # 当前用户的提醒都被删除

class ReminderSerializerTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.request = self.factory.get('/')
        self.request.user = self.user
        self.reminder_data = {
            'title': '测试提醒',
            'content': '测试内容',
            'reminder_type': 'CUSTOM',
            'reminder_method': 'EMAIL',
            'reminder_time': timezone.now() + timedelta(days=1)
        }
        self.serializer = ReminderSerializer(data=self.reminder_data, context={'request': self.request})

    def test_serializer_valid_data(self):
        """测试序列化器有效数据"""
        self.assertTrue(self.serializer.is_valid())

    def test_serializer_invalid_data(self):
        """测试序列化器无效数据"""
        invalid_data = self.reminder_data.copy()
        invalid_data.pop('title')
        serializer = ReminderSerializer(data=invalid_data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())

class ReminderViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.reminder = Reminder.objects.create(
            user=self.user,
            title='测试提醒',
            content='测试内容',
            reminder_type='CUSTOM',
            reminder_method='EMAIL',
            reminder_time=timezone.now() + timedelta(days=1)
        )
        self.other_reminder = Reminder.objects.create(
            user=self.other_user,
            title='其他用户的提醒',
            content='其他用户的内容',
            reminder_type='CUSTOM',
            reminder_method='EMAIL',
            reminder_time=timezone.now() + timedelta(days=1)
        )
        self.list_url = reverse("reminder-list")
        self.detail_url = reverse("reminder-detail", kwargs={"pk": self.reminder.id})

    def test_list_reminders(self):
        """测试获取提醒列表"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # 只能看到自己的提醒

    def test_create_reminder(self):
        """测试创建提醒"""
        data = {
            'title': '新提醒',
            'content': '新内容',
            'reminder_type': 'CUSTOM',
            'reminder_method': 'EMAIL',
            'reminder_time': (timezone.now() + timedelta(days=1)).isoformat()
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reminder.objects.count(), 3)  # 包括其他用户的提醒

    def test_update_reminder(self):
        """测试更新提醒"""
        data = {'title': '更新的提醒'}
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reminder.refresh_from_db()
        self.assertEqual(self.reminder.title, '更新的提醒')

    def test_delete_reminder(self):
        """测试删除提醒"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Reminder.objects.count(), 1)  # 只删除了自己的提醒

    def test_upcoming_reminders(self):
        """测试获取即将到来的提醒"""
        # 删除所有现有的提醒
        Reminder.objects.all().delete()

        # 创建一个过去的提醒（直接使用update方法绕过验证）
        past_reminder = Reminder.objects.create(
            user=self.user,
            title="过去的提醒",
            content="这是一个过去的提醒",
            reminder_time=timezone.now() + timezone.timedelta(days=1)
        )
        Reminder.objects.filter(id=past_reminder.id).update(
            reminder_time=timezone.now() - timezone.timedelta(days=1)
        )

        # 创建一个未来的提醒
        future_reminder = Reminder.objects.create(
            user=self.user,
            title="未来的提醒",
            content="这是一个未来的提醒",
            reminder_time=timezone.now() + timezone.timedelta(days=2)
        )

        response = self.client.get(f"{self.list_url}upcoming/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], future_reminder.id)

    def test_filter_by_reminder_type(self):
        """测试按提醒类型筛选"""
        response = self.client.get(f'{self.list_url}?reminder_type=CUSTOM')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_reminder_method(self):
        """测试按提醒方式筛选"""
        response = self.client.get(f'{self.list_url}?reminder_method=EMAIL')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_time_range(self):
        """测试按时间范围筛选"""
        start_time = (timezone.now() - timedelta(days=1)).isoformat()
        end_time = (timezone.now() + timedelta(days=2)).isoformat()
        response = self.client.get(f'{self.list_url}?start_time={start_time}&end_time={end_time}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_search_by_title(self):
        """测试按标题搜索"""
        response = self.client.get(f'{self.list_url}?search=测试')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_search_by_content(self):
        """测试按内容搜索"""
        response = self.client.get(f'{self.list_url}?search=内容')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_toggle_active(self):
        """测试切换提醒激活状态"""
        response = self.client.post(f'{self.detail_url}toggle_active/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reminder.refresh_from_db()
        self.assertFalse(self.reminder.is_active)

    def test_bulk_delete(self):
        """测试批量删除提醒"""
        # 创建API客户端并认证
        client = APIClient()
        client.force_authenticate(user=self.user)
        
        # 删除所有提醒
        Reminder.objects.all().delete()
        
        # 创建两个提醒
        reminder1 = Reminder.objects.create(
            user=self.user,
            title='测试提醒1',
            content='内容1',
            reminder_type='CUSTOM',
            reminder_method='EMAIL',
            reminder_time=timezone.now() + timezone.timedelta(days=1)
        )
        
        reminder2 = Reminder.objects.create(
            user=self.user,
            title='测试提醒2',
            content='内容2',
            reminder_type='CUSTOM',
            reminder_method='EMAIL',
            reminder_time=timezone.now() + timezone.timedelta(days=2)
        )
        
        # 批量删除提醒
        data = {'reminder_ids': [reminder1.id, reminder2.id]}
        response = client.post('/api/reminders/bulk_delete/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Reminder.objects.filter(user=self.user).count(), 0)  # 当前用户的提醒都被删除

    def test_bulk_delete_empty_list(self):
        """测试批量删除空列表"""
        data = {'reminder_ids': []}
        response = self.client.post(f'{self.list_url}bulk_delete/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_update(self):
        """测试批量更新提醒"""
        reminder_time = timezone.now() + timedelta(days=1)
        data = {
            'reminder_updates': [{
                'id': self.reminder.id,
                'title': '批量更新的提醒',
                'content': '更新的内容',
                'reminder_type': 'CUSTOM',
                'reminder_method': 'EMAIL',
                'reminder_time': reminder_time.isoformat(),
                'is_active': True
            }]
        }
        response = self.client.post(f'{self.list_url}bulk_update/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reminder.refresh_from_db()
        self.assertEqual(self.reminder.title, '批量更新的提醒')
        self.assertEqual(self.reminder.content, '更新的内容')

    def test_bulk_update_empty_list(self):
        """测试批量更新空列表"""
        data = {'reminder_updates': []}
        response = self.client.post(f'{self.list_url}bulk_update/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_update_invalid_data(self):
        """测试批量更新无效数据"""
        data = {
            'reminder_updates': [{
                'id': self.reminder.id,
                'reminder_time': 'invalid_time'
            }]
        }
        response = self.client.post(f'{self.list_url}bulk_update/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  # 无效数据应该返回400错误
        self.assertIn('error', response.data)  # 应该包含错误信息

    def test_unauthorized_access(self):
        """测试未授权访问"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_other_user_reminder(self):
        """测试访问其他用户的提醒"""
        other_detail_url = f'/api/reminders/{self.other_reminder.id}/'
        response = self.client.get(other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_other_user_reminder(self):
        """测试更新其他用户的提醒"""
        other_detail_url = f'/api/reminders/{self.other_reminder.id}/'
        data = {'title': '尝试更新'}
        response = self.client.patch(other_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_other_user_reminder(self):
        """测试删除其他用户的提醒"""
        other_detail_url = f'/api/reminders/{self.other_reminder.id}/'
        response = self.client.delete(other_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_reminder_invalid_time(self):
        """测试创建过期提醒"""
        data = {
            'title': '过期提醒',
            'content': '测试内容',
            'reminder_type': 'CUSTOM',
            'reminder_method': 'EMAIL',
            'reminder_time': (timezone.now() - timedelta(days=1)).isoformat()
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reminder_missing_required_fields(self):
        """测试创建缺少必需字段的提醒"""
        data = {
            'title': '缺少字段的提醒'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_task(self):
        """测试按关联任务筛选"""
        task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending",
        )
        self.reminder.related_task = task
        self.reminder.save()

        response = self.client.get(f"{self.list_url}?task_id={task.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["related_task"], task.id)

    def test_filter_by_activity(self):
        """测试按关联活动筛选"""
        task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending",
        )
        activity = PomodoroActivity.objects.create(
            user=self.user,
            title="测试活动",
            description="测试描述",
            status="not_started",
            task=task,
        )
        self.reminder.related_activity = activity
        self.reminder.save()

        response = self.client.get(f"{self.list_url}?activity_id={activity.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["related_activity"], activity.id)

    def test_filter_by_invalid_time_range(self):
        """测试无效的时间范围筛选"""
        response = self.client.get(
            f"{self.list_url}?start_time=invalid&end_time=invalid"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # 应该返回所有提醒

    def test_search_by_title_and_content(self):
        """测试按标题和内容搜索"""
        response = self.client.get(f"{self.list_url}?search=测试")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "测试提醒")

    def test_toggle_active(self):
        """测试切换提醒激活状态"""
        response = self.client.post(f"{self.detail_url}toggle_active/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_active"])

        response = self.client.post(f"{self.detail_url}toggle_active/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_active"])

    def test_bulk_delete_validation(self):
        """测试批量删除的验证"""
        # 测试空列表
        response = self.client.post(f"{self.list_url}bulk_delete/", {"reminder_ids": []})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

        # 测试无效ID
        response = self.client.post(
            f"{self.list_url}bulk_delete/", {"reminder_ids": [999]}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)

    def test_bulk_update_validation(self):
        """测试批量更新的验证"""
        # 创建两个提醒
        reminder1 = Reminder.objects.create(
            user=self.user,
            title="提醒1",
            content="内容1",
            reminder_time=timezone.now() + timezone.timedelta(days=1)
        )
        reminder2 = Reminder.objects.create(
            user=self.user,
            title="提醒2",
            content="内容2",
            reminder_time=timezone.now() + timezone.timedelta(days=2)
        )

        # 测试批量更新
        data = {
            "reminder_updates": [
                {"id": reminder1.id, "title": "更新后的提醒1"},
                {"id": reminder2.id, "title": "更新后的提醒2"}
            ]
        }
        response = self.client.post(f"{self.list_url}bulk_update/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证更新结果
        reminder1.refresh_from_db()
        reminder2.refresh_from_db()
        self.assertEqual(reminder1.title, "更新后的提醒1")
        self.assertEqual(reminder2.title, "更新后的提醒2")

    def test_cross_user_access(self):
        """测试跨用户访问"""
        other_user = User.objects.create_user(
            username="otheruser2",  # 修改用户名避免重复
            email="otheruser2@example.com",
            password="testpass123"
        )
        other_reminder = Reminder.objects.create(
            user=other_user,
            title="其他用户的提醒",
            content="测试内容",
            reminder_time=timezone.now() + timezone.timedelta(days=1)
        )

        # 尝试访问其他用户的提醒
        response = self.client.get(f"{self.detail_url}{other_reminder.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
