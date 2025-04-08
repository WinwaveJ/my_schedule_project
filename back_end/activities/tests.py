from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from tasks.models import Task
from app_settings.models import AppSettings
from .models import Activity
from datetime import datetime, date, time as datetime_time
from django.test import RequestFactory
from .serializers import ActivitySerializer
from django.core.exceptions import ValidationError
import time  # 添加time模块导入
from django.urls import reverse

User = get_user_model()


class ActivityTests(APITestCase):
    def setUp(self):
        """测试设置"""
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="testpass123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # 创建任务
        self.task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending"
        )

        # 创建活动
        self.activity = Activity.objects.create(
            user=self.user,
            title="测试活动",
            description="测试描述",
            timer_type="pomodoro",  # 设置为番茄钟模式
            status="not_started",
            task=self.task
        )

        self.list_url = "/api/activities/"
        self.detail_url = f"{self.list_url}{self.activity.id}/"

        # 创建测试设置
        self.settings = AppSettings.objects.create(
            user=self.user,
            pomodoro_duration=25,
            short_break_duration=5,
            long_break_duration=15,
            long_break_interval=4,
            daily_pomodoro_goal=8,
            daily_stopwatch_goal=120,
        )

        # 创建测试任务
        self.task = Task.objects.create(
            title="Test Task",
            description="Test Description",
            user=self.user,
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
        )

        # 创建测试活动
        self.activity = Activity.objects.create(
            title="Test Activity",
            description="Test Description",
            user=self.user,
            task=self.task,
            timer_type="POMODORO",
            status="PENDING",
        )

    def test_activity_creation(self):
        """测试活动创建"""
        # 创建一个任务
        task = Task.objects.create(
            title="测试任务",
            description="这是一个测试任务",
            user=self.user,
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="NOT_URGENT_NOT_IMPORTANT",
            status="PENDING",
        )

        # 创建活动
        activity = Activity.objects.create(
            task=task,
            user=self.user,
            title="测试活动",
            description="测试活动描述",
            duration=timezone.timedelta(minutes=30),
            status="COMPLETED",
        )

        self.assertEqual(activity.task, task)
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.duration, timezone.timedelta(minutes=30))
        self.assertEqual(activity.status, "COMPLETED")

    def test_activity_list(self):
        """测试活动列表获取"""
        # 删除所有现有的活动
        Activity.objects.all().delete()

        # 创建一个新活动
        task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending"
        )
        activity = Activity.objects.create(
            user=self.user,
            title="测试活动",
            description="测试描述",
            timer_type="pomodoro",
            status="not_started",
            task=task
        )

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], activity.id)

    def test_activity_filter(self):
        """测试活动筛选"""
        # 删除所有现有的活动
        Activity.objects.all().delete()

        # 创建一个新活动
        task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending"
        )
        activity = Activity.objects.create(
            user=self.user,
            title="测试活动",
            description="测试描述",
            timer_type="pomodoro",
            status="not_started",
            task=task
        )

        # 按标题搜索
        response = self.client.get(f"{self.list_url}?search=测试")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], activity.id)

    def test_activity_update(self):
        """测试活动更新"""
        data = {"title": "Updated Activity", "description": "Updated Description"}
        response = self.client.patch(
            f"/api/activities/{self.activity.id}/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Activity")

    def test_activity_delete(self):
        """测试活动删除"""
        # 删除所有现有的活动
        Activity.objects.all().delete()

        # 创建一个新活动
        task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending"
        )
        activity = Activity.objects.create(
            user=self.user,
            title="测试活动",
            description="测试描述",
            timer_type="pomodoro",
            status="not_started",
            task=task
        )

        # 删除活动
        response = self.client.delete(f"{self.list_url}{activity.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Activity.objects.count(), 0)

    def test_pomodoro_operations(self):
        """测试番茄钟相关操作"""
        # 开始番茄钟
        response = self.client.post(
            f"/api/activities/{self.activity.id}/start_pomodoro/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "IN_PROGRESS")
        self.assertIsNotNone(self.activity.current_pomodoro_start)

        # 开始休息
        response = self.client.post(
            f"/api/activities/{self.activity.id}/start_break/", {"is_long_break": False}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "PAUSED")
        self.assertIsNotNone(self.activity.current_break_start)

        # 完成番茄钟
        response = self.client.post(
            f"/api/activities/{self.activity.id}/complete_pomodoro/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, "PAUSED")
        self.assertEqual(self.activity.pomodoro_count, 1)

    def test_stopwatch_operations(self):
        """测试秒表相关操作"""
        # 创建秒表活动
        stopwatch_activity = Activity.objects.create(
            title="Stopwatch Activity",
            description="Test Description",
            user=self.user,
            task=self.task,
            timer_type="STOPWATCH",
            status="PENDING",
        )

        # 开始秒表
        response = self.client.post(
            f"/api/activities/{stopwatch_activity.id}/start_stopwatch/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stopwatch_activity.refresh_from_db()
        self.assertEqual(stopwatch_activity.status, "IN_PROGRESS")
        self.assertIsNotNone(stopwatch_activity.start_time)

        # 停止秒表
        response = self.client.post(
            f"/api/activities/{stopwatch_activity.id}/stop_stopwatch/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stopwatch_activity.refresh_from_db()
        self.assertEqual(stopwatch_activity.status, "COMPLETED")
        self.assertIsNotNone(stopwatch_activity.end_time)

    def test_bulk_operations(self):
        """测试批量操作"""
        # 删除所有现有的活动
        Activity.objects.all().delete()

        # 创建两个活动
        task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending"
        )
        activity1 = Activity.objects.create(
            user=self.user,
            title="活动1",
            description="描述1",
            timer_type="pomodoro",
            status="not_started",
            task=task
        )
        activity2 = Activity.objects.create(
            user=self.user,
            title="活动2",
            description="描述2",
            timer_type="pomodoro",
            status="not_started",
            task=task
        )

        # 测试批量删除
        response = self.client.post(
            f"{self.list_url}bulk_delete/",
            {"activity_ids": [activity1.id, activity2.id]},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Activity.objects.count(), 0)

        # 重新创建活动用于测试批量更新
        activity1 = Activity.objects.create(
            user=self.user,
            title="活动1",
            description="描述1",
            timer_type="pomodoro",
            status="not_started",
            task=task
        )
        activity2 = Activity.objects.create(
            user=self.user,
            title="活动2",
            description="描述2",
            timer_type="pomodoro",
            status="not_started",
            task=task
        )

        # 测试批量更新
        response = self.client.post(
            f"{self.list_url}bulk_update/",
            {
                "activity_updates": [
                    {"id": activity1.id, "title": "更新后的活动1"},
                    {"id": activity2.id, "title": "更新后的活动2"}
                ]
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证更新结果
        activity1.refresh_from_db()
        activity2.refresh_from_db()
        self.assertEqual(activity1.title, "更新后的活动1")
        self.assertEqual(activity2.title, "更新后的活动2")

    def test_activity_duration_calculation(self):
        """测试活动时长计算"""
        # 创建一个任务
        task = Task.objects.create(
            title="测试任务",
            description="这是一个测试任务",
            user=self.user,
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="NOT_URGENT_NOT_IMPORTANT",
            status="PENDING",
        )

        # 创建一个活动
        activity = Activity.objects.create(
            title="测试活动",
            description="这是一个测试活动",
            user=self.user,
            task=task,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=2),
            duration=timezone.timedelta(hours=2),
            status="COMPLETED",
        )

        # 验证时长计算是否正确
        expected_duration = timezone.timedelta(hours=2)
        self.assertEqual(
            activity.duration.total_seconds(), expected_duration.total_seconds()
        )

    def test_activity_task_association(self):
        """测试活动与任务的关联"""
        # 创建一个任务
        task = Task.objects.create(
            title="测试任务",
            description="这是一个测试任务",
            user=self.user,
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=2),
            priority="NOT_URGENT_NOT_IMPORTANT",
            status="PENDING",
        )

        # 创建一个关联到任务的活动
        activity = Activity.objects.create(
            user=self.user,
            task=task,
            start_time=timezone.now() - timezone.timedelta(hours=1),
            end_time=timezone.now(),
            duration=timezone.timedelta(hours=1),
            status="COMPLETED",
        )

        # 验证活动与任务的关联
        self.assertEqual(activity.task, task)
        self.assertIn(activity, task.activities.all())

    def test_activity_statistics(self):
        """测试活动统计功能"""
        # 创建一个任务
        task = Task.objects.create(
            title="测试任务",
            description="这是一个测试任务",
            user=self.user,
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="NOT_URGENT_NOT_IMPORTANT",
            status="PENDING",
        )

        # 创建一些测试活动
        today = timezone.now().date()
        Activity.objects.create(
            title="活动1",
            user=self.user,
            task=task,
            start_time=timezone.make_aware(datetime.combine(today, datetime_time.min)),
            end_time=timezone.make_aware(datetime.combine(today, datetime_time.min))
            + timezone.timedelta(hours=2),
            duration=timezone.timedelta(hours=2),
            status="COMPLETED",
        )
        Activity.objects.create(
            title="活动2",
            user=self.user,
            task=task,
            start_time=timezone.make_aware(datetime.combine(today, datetime_time.min))
            + timezone.timedelta(hours=3),
            end_time=timezone.make_aware(datetime.combine(today, datetime_time.min))
            + timezone.timedelta(hours=5),
            duration=timezone.timedelta(hours=2),
            status="COMPLETED",
        )

        # 获取今天的活动
        today_activities = Activity.objects.filter(
            user=self.user, start_time__date=today, status="COMPLETED"
        )

        # 计算总时长（转换为秒）
        total_duration = sum(
            activity.duration.total_seconds() for activity in today_activities
        )
        self.assertEqual(total_duration, 14400)  # 4小时 = 14400秒

    def test_activity_status_transitions(self):
        """测试活动状态转换"""
        # 创建活动
        activity = Activity.objects.create(
            user=self.user,
            task=self.task,
            title='测试活动',
            description='测试描述',
            timer_type='POMODORO'
        )

        # 测试状态转换
        self.assertEqual(activity.status, 'PENDING')
        
        # 开始活动
        activity.status = 'IN_PROGRESS'
        activity.save()
        self.assertEqual(activity.status, 'IN_PROGRESS')
        
        # 暂停活动
        activity.status = 'PAUSED'
        activity.save()
        self.assertEqual(activity.status, 'PAUSED')
        
        # 恢复活动
        activity.status = 'IN_PROGRESS'
        activity.save()
        self.assertEqual(activity.status, 'IN_PROGRESS')
        
        # 完成活动
        activity.status = 'COMPLETED'
        activity.save()
        self.assertEqual(activity.status, 'COMPLETED')
        
        # 取消活动
        activity.status = 'CANCELLED'
        activity.save()
        self.assertEqual(activity.status, 'CANCELLED')

    def test_pomodoro_timer(self):
        """测试番茄钟计时功能"""
        # 创建番茄钟活动
        activity = Activity.objects.create(
            user=self.user,
            task=self.task,
            title='番茄钟测试',
            description='测试番茄钟功能',
            timer_type='POMODORO'
        )

        # 测试开始番茄钟
        activity.start_pomodoro()
        self.assertIsNotNone(activity.current_pomodoro_start)
        self.assertEqual(activity.status, 'IN_PROGRESS')

        # 测试开始休息
        activity.start_break(is_long_break=False)
        self.assertTrue(activity.is_break)
        self.assertFalse(activity.is_long_break)
        self.assertIsNotNone(activity.current_break_start)

        # 测试开始长休息
        activity.start_break(is_long_break=True)
        self.assertTrue(activity.is_break)
        self.assertTrue(activity.is_long_break)

        # 测试完成番茄钟
        activity.complete_pomodoro()
        self.assertEqual(activity.pomodoro_count, 1)
        self.assertFalse(activity.is_break)
        self.assertFalse(activity.is_long_break)
        self.assertIsNone(activity.current_pomodoro_start)
        self.assertIsNone(activity.current_break_start)

    def test_stopwatch_timer(self):
        """测试正计时功能"""
        # 创建正计时活动
        activity = Activity.objects.create(
            user=self.user,
            task=self.task,
            title='正计时测试',
            description='测试正计时功能',
            timer_type='STOPWATCH'
        )

        # 测试开始计时
        activity.start_stopwatch()
        self.assertIsNotNone(activity.start_time)
        self.assertEqual(activity.status, 'IN_PROGRESS')

        # 测试暂停计时
        activity.status = 'PAUSED'
        activity.save()
        self.assertEqual(activity.status, 'PAUSED')

        # 测试继续计时
        activity.status = 'IN_PROGRESS'
        activity.save()
        self.assertEqual(activity.status, 'IN_PROGRESS')

        # 测试停止计时
        activity.stop_stopwatch()
        self.assertIsNotNone(activity.end_time)
        self.assertIsNotNone(activity.duration)
        self.assertEqual(activity.status, 'COMPLETED')

    def test_timer_type_validation(self):
        """测试计时类型验证"""
        # 测试番茄钟模式
        activity = Activity.objects.create(
            user=self.user,
            task=self.task,
            title='番茄钟测试',
            description='测试番茄钟验证',
            timer_type='POMODORO'
        )

        # 验证番茄钟模式不能设置正计时字段
        with self.assertRaises(ValidationError):
            activity.start_time = timezone.now()
            activity.end_time = timezone.now() + timezone.timedelta(hours=1)
            activity.duration = timezone.timedelta(hours=1)
            activity.full_clean()

        # 测试正计时模式
        activity = Activity.objects.create(
            user=self.user,
            task=self.task,
            title='正计时测试',
            description='测试正计时验证',
            timer_type='STOPWATCH'
        )

        # 验证正计时模式不能设置番茄钟字段
        with self.assertRaises(ValidationError):
            activity.pomodoro_count = 1
            activity.current_pomodoro_start = timezone.now()
            activity.current_break_start = timezone.now()
            activity.full_clean()

    def test_activity_time_calculations(self):
        """测试活动时间计算"""
        # 创建正计时活动
        activity = Activity.objects.create(
            user=self.user,
            task=self.task,
            title='时间计算测试',
            description='测试时间计算功能',
            timer_type='STOPWATCH'
        )

        # 开始计时
        start_time = timezone.now()
        activity.start_stopwatch()
        
        # 等待一段时间
        time.sleep(2)
        
        # 测试已用时间计算
        elapsed_time = activity.get_elapsed_time()
        self.assertGreater(elapsed_time.total_seconds(), 0)
        
        # 测试剩余时间计算
        remaining_time = activity.get_remaining_time()
        self.assertIsNone(remaining_time)  # 正计时模式下没有剩余时间

        # 停止计时
        activity.stop_stopwatch()
        
        # 验证持续时间
        self.assertIsNotNone(activity.duration)
        self.assertEqual(activity.duration, activity.end_time - activity.start_time)

    def test_activity_ordering(self):
        """测试活动排序"""
        # 删除已有的活动
        Activity.objects.all().delete()
        
        base_time = timezone.now()
        
        # 创建多个活动
        activity1 = Activity.objects.create(
            user=self.user,
            task=self.task,
            title='Test Activity 1',
            description='描述1',
            timer_type='POMODORO',
            created_at=base_time
        )

        activity2 = Activity.objects.create(
            user=self.user,
            task=self.task,
            title='Test Activity 2',
            description='描述2',
            timer_type='STOPWATCH',
            created_at=base_time + timezone.timedelta(minutes=1)
        )

        activity3 = Activity.objects.create(
            user=self.user,
            task=self.task,
            title='Test Activity 3',
            description='描述3',
            timer_type='POMODORO',
            created_at=base_time + timezone.timedelta(minutes=2)
        )

        # 验证按创建时间倒序排序
        activities = list(Activity.objects.all().order_by('-created_at'))
        self.assertEqual(activities[0].title, 'Test Activity 3')  # 最新
        self.assertEqual(activities[1].title, 'Test Activity 2')  # 中间
        self.assertEqual(activities[2].title, 'Test Activity 1')  # 最早


class ActivitySerializerTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
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
        self.request = self.factory.get('/')
        self.request.user = self.user
        
        # 创建测试任务
        self.task = Task.objects.create(
            title='测试任务',
            description='测试描述',
            user=self.user,
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1)
        )
        self.other_task = Task.objects.create(
            title='其他用户的任务',
            description='其他用户的描述',
            user=self.other_user,
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1)
        )
        
        self.activity_data = {
            'title': '测试活动',
            'description': '测试描述',
            'task_id': self.task.id,
            'status': 'PENDING',
            'timer_type': 'POMODORO'
        }
        self.serializer = ActivitySerializer(data=self.activity_data, context={'request': self.request})

    def test_serializer_valid_data(self):
        """测试序列化器有效数据"""
        self.assertTrue(self.serializer.is_valid())

    def test_serializer_invalid_task_id(self):
        """测试无效的任务ID"""
        invalid_data = self.activity_data.copy()
        invalid_data['task_id'] = 99999  # 不存在的任务ID
        serializer = ActivitySerializer(data=invalid_data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('task_id', serializer.errors)

    def test_serializer_other_user_task(self):
        """测试使用其他用户的任务"""
        invalid_data = self.activity_data.copy()
        invalid_data['task_id'] = self.other_task.id
        serializer = ActivitySerializer(data=invalid_data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('task_id', serializer.errors)

    def test_serializer_missing_required_fields(self):
        """测试缺少必需字段"""
        invalid_data = {'title': '测试活动'}  # 缺少task_id
        serializer = ActivitySerializer(data=invalid_data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('task_id', serializer.errors)

    def test_serializer_invalid_status(self):
        """测试无效的状态值"""
        invalid_data = self.activity_data.copy()
        invalid_data['status'] = 'INVALID_STATUS'
        serializer = ActivitySerializer(data=invalid_data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)

    def test_serializer_invalid_timer_type(self):
        """测试无效的计时类型"""
        invalid_data = self.activity_data.copy()
        invalid_data['timer_type'] = 'INVALID_TYPE'
        serializer = ActivitySerializer(data=invalid_data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('timer_type', serializer.errors)

    def test_serializer_create(self):
        """测试创建活动"""
        self.assertTrue(self.serializer.is_valid())
        activity = self.serializer.save()
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.task, self.task)
        self.assertEqual(activity.title, '测试活动')

    def test_serializer_update(self):
        """测试更新活动"""
        activity = Activity.objects.create(
            title='原始标题',
            description='原始描述',
            user=self.user,
            task=self.task,
            status='PENDING',
            timer_type='POMODORO'
        )
        update_data = {
            'title': '更新后的标题',
            'description': '更新后的描述'
        }
        serializer = ActivitySerializer(activity, data=update_data, partial=True, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        updated_activity = serializer.save()
        self.assertEqual(updated_activity.title, '更新后的标题')
        self.assertEqual(updated_activity.description, '更新后的描述')
        self.assertEqual(updated_activity.task, self.task)  # 确保任务没有改变


class ActivityViewSetTests(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse("activity-list")
        self.detail_url = reverse("activity-detail", kwargs={"pk": 1})

        # 创建测试任务
        self.task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending"
        )

        # 创建测试活动
        self.activity = Activity.objects.create(
            user=self.user,
            title="测试活动",
            description="测试描述",
            timer_type="pomodoro",
            status="not_started",
            task=self.task
        )

    def test_filter_by_task(self):
        """测试按任务筛选活动"""
        task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending"
        )
        activity = Activity.objects.create(
            user=self.user,
            title="任务相关活动",
            description="测试描述",
            timer_type="pomodoro",
            status="not_started",
            task=task
        )

        response = self.client.get(f"{self.list_url}?task_id={task.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], activity.id)

    def test_filter_by_status(self):
        """测试按状态筛选活动"""
        response = self.client.get(f"{self.list_url}?status=not_started")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], "not_started")

    def test_filter_by_timer_type(self):
        """测试按计时类型筛选活动"""
        response = self.client.get(f"{self.list_url}?timer_type=pomodoro")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["timer_type"], "pomodoro")

    def test_filter_by_date_range(self):
        """测试按日期范围筛选"""
        # 创建不同日期的活动
        yesterday = timezone.now() - timezone.timedelta(days=1)
        tomorrow = timezone.now() + timezone.timedelta(days=1)

        # 创建昨天的活动
        activity1 = Activity.objects.create(
            user=self.user,
            title="昨天的活动",
            description="昨天的描述",
            timer_type="pomodoro",
            status="not_started",
            task=self.task
        )
        Activity.objects.filter(pk=activity1.pk).update(created_at=yesterday)
        
        # 创建明天的活动
        activity2 = Activity.objects.create(
            user=self.user,
            title="明天的活动",
            description="明天的描述",
            timer_type="pomodoro",
            status="not_started",
            task=self.task
        )
        Activity.objects.filter(pk=activity2.pk).update(created_at=tomorrow)

        # 按日期范围筛选
        response = self.client.get(
            f"{self.list_url}?start_date={yesterday.date()}&end_date={tomorrow.date()}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # 包括原始活动

    def test_search_by_title_and_description(self):
        """测试按标题和描述搜索活动"""
        response = self.client.get(f"{self.list_url}?search=测试")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "测试活动")

    def test_start_pomodoro_validation(self):
        """测试开始番茄钟的验证"""
        # 删除所有现有的活动
        Activity.objects.all().delete()

        # 创建一个非番茄钟活动
        task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending"
        )
        activity = Activity.objects.create(
            user=self.user,
            title="测试活动",
            description="测试描述",
            timer_type="stopwatch",  # 设置为秒表模式
            status="not_started",
            task=task
        )

        # 尝试开始番茄钟
        response = self.client.post(f"{self.list_url}{activity.id}/start_pomodoro/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_start_break_validation(self):
        """测试开始休息的验证"""
        # 删除所有现有的活动
        Activity.objects.all().delete()

        # 创建一个非番茄钟活动
        task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending"
        )
        activity = Activity.objects.create(
            user=self.user,
            title="测试活动",
            description="测试描述",
            timer_type="stopwatch",  # 设置为秒表模式
            status="not_started",
            task=task
        )

        # 尝试开始休息
        response = self.client.post(f"{self.list_url}{activity.id}/start_break/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_complete_pomodoro_validation(self):
        """测试完成番茄钟的验证"""
        # 删除所有现有的活动
        Activity.objects.all().delete()

        # 创建一个非番茄钟活动
        task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending"
        )
        activity = Activity.objects.create(
            user=self.user,
            title="测试活动",
            description="测试描述",
            timer_type="stopwatch",  # 设置为秒表模式
            status="not_started",
            task=task
        )

        # 尝试完成番茄钟
        response = self.client.post(f"{self.list_url}{activity.id}/complete_pomodoro/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stopwatch_validation(self):
        """测试秒表操作的验证"""
        # 删除所有现有的活动
        Activity.objects.all().delete()

        # 创建一个番茄钟活动
        task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending"
        )
        activity = Activity.objects.create(
            user=self.user,
            title="测试活动",
            description="测试描述",
            timer_type="pomodoro",  # 设置为番茄钟模式
            status="not_started",
            task=task
        )

        # 尝试使用秒表操作
        response = self.client.post(f"{self.list_url}{activity.id}/start_stopwatch/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_delete_validation(self):
        """测试批量删除的验证"""
        # 测试空列表
        response = self.client.post(f"{self.list_url}bulk_delete/", {"activity_ids": []})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

        # 测试无效ID
        response = self.client.post(
            f"{self.list_url}bulk_delete/", {"activity_ids": [999]}
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_bulk_update_validation(self):
        """测试批量更新的验证"""
        # 创建两个活动
        task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending"
        )
        activity1 = Activity.objects.create(
            user=self.user,
            title="活动1",
            description="描述1",
            timer_type="pomodoro",
            status="not_started",
            task=task
        )
        activity2 = Activity.objects.create(
            user=self.user,
            title="活动2",
            description="描述2",
            timer_type="pomodoro",
            status="not_started",
            task=task
        )

        # 测试批量更新
        data = {
            "activity_updates": [
                {"id": activity1.id, "title": "更新后的活动1"},
                {"id": activity2.id, "title": "更新后的活动2"}
            ]
        }
        response = self.client.post(f"{self.list_url}bulk_update/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证更新结果
        activity1.refresh_from_db()
        activity2.refresh_from_db()
        self.assertEqual(activity1.title, "更新后的活动1")
        self.assertEqual(activity2.title, "更新后的活动2")

    def test_unauthorized_access(self):
        """测试未授权访问"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cross_user_access(self):
        """测试跨用户访问"""
        other_user = User.objects.create_user(
            username="otheruser",
            email="otheruser@example.com",
            password="testpass123"
        )
        # 创建任务
        task = Task.objects.create(
            user=other_user,
            title="测试任务",
            description="测试任务描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending"
        )
        # 创建活动
        other_activity = Activity.objects.create(
            user=other_user,
            title="其他用户的活动",
            description="测试描述",
            timer_type="pomodoro",
            status="not_started",
            task=task
        )

        # 尝试访问其他用户的活动
        response = self.client.get(f"{self.detail_url}{other_activity.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
