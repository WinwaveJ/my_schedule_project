from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Task, TaskTag
from .serializers import TaskSerializer
from django.urls import reverse
from datetime import datetime, timedelta
from rest_framework import serializers
from app_settings.models import AppSettings, TaskCategory
from activities.models import PomodoroActivity, StopwatchActivity

User = get_user_model()


class TaskTests(APITestCase):
    def setUp(self):
        # 创建测试用户
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="testpass123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # 创建测试标签
        self.tag = TaskTag.objects.create(name="Test Tag", user=self.user)

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
        self.task.tags.add(self.tag)

        # 创建测试活动
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

    def test_task_creation(self):
        """测试任务创建"""
        url = reverse("task-list")
        due_date = timezone.now() + timezone.timedelta(days=1)
        data = {
            "title": "测试任务",
            "description": "这是一个测试任务",
            "due_date": due_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "estimated_duration": int(timezone.timedelta(hours=1).total_seconds()),
            "priority": "NOT_URGENT_NOT_IMPORTANT",
            "status": "PENDING",
            "tag_ids": [self.tag.id],
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 2)  # 包括 setUp 中创建的任务
        self.assertEqual(response.data["title"], "测试任务")
        self.assertEqual(len(response.data["tags"]), 1)

    def test_task_list(self):
        """测试任务列表获取"""
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_task_filter(self):
        """测试任务筛选"""
        # 按标签筛选
        response = self.client.get(f"/api/tasks/?tag_ids={self.tag.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        # 按标题搜索
        response = self.client.get("/api/tasks/?search=Test")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_task_update(self):
        """测试任务更新"""
        data = {"title": "Updated Task", "description": "Updated Description"}
        response = self.client.patch(f"/api/tasks/{self.task.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Task")

    def test_task_delete(self):
        """测试任务删除"""
        response = self.client.delete(f"/api/tasks/{self.task.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 0)

    def test_bulk_operations(self):
        """测试批量操作"""
        # 创建第二个任务
        task2 = Task.objects.create(
            title="Second Task",
            description="Second Description",
            user=self.user,
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
        )

        # 测试批量删除
        response = self.client.post(
            "/api/tasks/bulk_delete/",
            {"task_ids": [self.task.id, task2.id]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 0)

        # 重新创建任务用于测试批量更新
        self.task = Task.objects.create(
            title="Task 1",
            description="Description 1",
            user=self.user,
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
        )
        task2 = Task.objects.create(
            title="Task 2",
            description="Description 2",
            user=self.user,
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
        )

        # 测试批量更新
        response = self.client.post(
            "/api/tasks/bulk_update/",
            {
                "task_updates": [
                    {"id": self.task.id, "title": "Updated Task 1"},
                    {"id": task2.id, "title": "Updated Task 2"},
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证更新结果
        self.task.refresh_from_db()
        task2.refresh_from_db()
        self.assertEqual(self.task.title, "Updated Task 1")
        self.assertEqual(task2.title, "Updated Task 2")

    def test_task_progress_calculation(self):
        """测试任务进度计算"""
        from activities.models import Activity

        # 创建一个任务
        task = Task.objects.create(
            title="测试进度任务",
            description="这是一个测试进度的任务",
            user=self.user,
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=2),
            priority="NOT_URGENT_NOT_IMPORTANT",
            status="PENDING",
        )

        # 创建一个已完成的活动
        Activity.objects.create(
            task=task,
            user=self.user,
            start_time=timezone.now() - timezone.timedelta(hours=1),
            end_time=timezone.now(),
            duration=timezone.timedelta(hours=1),
            status="COMPLETED",
        )

        # 更新任务进度
        task.update_progress()

        # 验证进度是否为50%
        self.assertEqual(task.progress, 50.0)

    def test_task_search_edge_cases(self):
        """测试任务搜索边界情况"""
        # 删除 setUp 中创建的任务
        self.task.delete()

        # 创建测试任务
        task1 = Task.objects.create(
            title="测试任务1",
            description="这是一个测试任务",
            user=self.user,
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="NOT_URGENT_NOT_IMPORTANT",
        )
        task2 = Task.objects.create(
            title="测试任务2",
            description="这是另一个测试任务",
            user=self.user,
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="NOT_URGENT_NOT_IMPORTANT",
        )

        # 测试空搜索
        response = self.client.get("/api/tasks/?search=")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # 测试特殊字符搜索
        response = self.client.get("/api/tasks/?search=!@#$%^&*()")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # 测试不存在的标签ID
        response = self.client.get("/api/tasks/?tag_ids=999")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_task_focused_duration(self):
        """测试任务专注时长计算"""
        # 完成一个番茄钟
        self.pomodoro_activity.pomodoro_count = 2
        self.pomodoro_activity.status = "COMPLETED"
        self.pomodoro_activity.save()

        # 完成一个正计时
        self.stopwatch_activity.start_time = timezone.now()
        self.stopwatch_activity.end_time = timezone.now() + timezone.timedelta(minutes=30)
        self.stopwatch_activity.duration = timezone.timedelta(minutes=30)
        self.stopwatch_activity.status = "COMPLETED"
        self.stopwatch_activity.save()

        # 计算总专注时长
        focused_duration = self.task.focused_duration
        self.assertEqual(focused_duration, 80)  # 2个番茄钟(50分钟) + 30分钟正计时


class TaskTagTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="testuser@example.com", password="testpass123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.tag = TaskTag.objects.create(name="Test Tag", user=self.user)

    def test_tag_creation(self):
        """测试标签创建"""
        data = {"name": "New Tag"}
        response = self.client.post("/api/tags/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TaskTag.objects.count(), 2)

    def test_tag_list(self):
        """测试标签列表获取"""
        response = self.client.get("/api/tags/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_tag_update(self):
        """测试标签更新"""
        data = {"name": "Updated Tag"}
        response = self.client.patch(f"/api/tags/{self.tag.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Tag")

    def test_tag_delete(self):
        """测试标签删除"""
        response = self.client.delete(f"/api/tags/{self.tag.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TaskTag.objects.count(), 0)


class TaskSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.tag = TaskTag.objects.create(user=self.user, name="测试标签")
        self.serializer = TaskSerializer(context={"request": type("Request", (), {"user": self.user})()})
        self.task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending"
        )

    def test_validate_due_date(self):
        """测试截止时间验证"""
        # 测试过去的日期
        past_date = timezone.now() - timezone.timedelta(days=1)
        with self.assertRaises(serializers.ValidationError):
            self.serializer.validate_due_date(past_date)

        # 测试未来的日期
        future_date = timezone.now() + timezone.timedelta(days=1)
        validated_date = self.serializer.validate_due_date(future_date)
        self.assertEqual(validated_date, future_date)

    def test_create_with_tags(self):
        """测试创建带标签的任务"""
        data = {
            "title": "测试任务",
            "description": "测试描述",
            "due_date": timezone.now() + timezone.timedelta(days=1),
            "estimated_duration": 3600,  # 1小时
            "priority": "high",
            "status": "pending",
            "tag_ids": [self.tag.id],
        }

        task = self.serializer.create(data)
        self.assertEqual(task.title, data["title"])
        self.assertEqual(task.description, data["description"])
        self.assertEqual(task.estimated_duration.total_seconds(), 3600)
        self.assertEqual(list(task.tags.all()), [self.tag])

    def test_create_without_tags(self):
        """测试创建不带标签的任务"""
        data = {
            "title": "测试任务",
            "description": "测试描述",
            "due_date": timezone.now() + timezone.timedelta(days=1),
            "estimated_duration": 3600,
            "priority": "high",
            "status": "pending",
        }

        task = self.serializer.create(data)
        self.assertEqual(task.title, data["title"])
        self.assertEqual(task.description, data["description"])
        self.assertEqual(task.estimated_duration.total_seconds(), 3600)
        self.assertEqual(list(task.tags.all()), [])

    def test_update_with_tags(self):
        """测试更新带标签的任务"""
        data = {
            "title": "更新后的任务",
            "description": "更新后的描述",
            "tag_ids": [self.tag.id]
        }
        updated_task = self.serializer.update(self.task, data)
        self.assertEqual(updated_task.title, "更新后的任务")
        self.assertEqual(updated_task.description, "更新后的描述")
        self.assertEqual(list(updated_task.tags.all()), [self.tag])

    def test_update_without_tags(self):
        """测试更新不带标签的任务"""
        task = Task.objects.create(
            user=self.user,
            title="原始任务",
            description="原始描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="low",
            status="pending",
        )

        data = {
            "title": "更新后的任务",
            "description": "更新后的描述",
        }

        updated_task = self.serializer.update(task, data)
        self.assertEqual(updated_task.title, data["title"])
        self.assertEqual(updated_task.description, data["description"])
        self.assertEqual(list(updated_task.tags.all()), [])

    def test_update_estimated_duration(self):
        """测试更新预计时长"""
        task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="low",
            status="pending",
        )

        data = {"estimated_duration": 7200}  # 2小时
        updated_task = self.serializer.update(task, data)
        self.assertEqual(updated_task.estimated_duration.total_seconds(), 7200)

    def test_serializer_fields(self):
        """测试序列化器字段"""
        task = Task.objects.create(
            user=self.user,
            title="测试任务",
            description="测试描述",
            due_date=timezone.now() + timezone.timedelta(days=1),
            estimated_duration=timezone.timedelta(hours=1),
            priority="high",
            status="pending",
        )
        task.tags.add(self.tag)

        serializer = TaskSerializer(task)
        data = serializer.data

        self.assertEqual(data["title"], task.title)
        self.assertEqual(data["description"], task.description)
        self.assertEqual(data["priority"], task.priority)
        self.assertEqual(data["status"], task.status)
        self.assertEqual(len(data["tags"]), 1)
        self.assertEqual(data["tags"][0]["name"], self.tag.name)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
        self.assertNotIn("tag_ids", data)  # tag_ids 是 write_only

    def test_validate_required_fields(self):
        """测试必填字段验证"""
        data = {
            "description": "测试描述",
            "due_date": timezone.now() + timezone.timedelta(days=1),
            "estimated_duration": 3600,
            "priority": "high",
            "status": "pending",
        }

        serializer = TaskSerializer(data=data, partial=False)
        self.assertFalse(serializer.is_valid())
        self.assertIn("title", serializer.errors)

    def test_validate_priority_choices(self):
        """测试优先级选项验证"""
        data = {
            "title": "测试任务",
            "description": "测试描述",
            "due_date": timezone.now() + timezone.timedelta(days=1),
            "estimated_duration": 3600,
            "priority": "invalid_priority",
            "status": "pending",
        }

        serializer = TaskSerializer(data=data, partial=False)
        self.assertFalse(serializer.is_valid())
        self.assertIn("priority", serializer.errors)

    def test_validate_status_choices(self):
        """测试状态选项验证"""
        data = {
            "title": "测试任务",
            "description": "测试描述",
            "due_date": timezone.now() + timezone.timedelta(days=1),
            "estimated_duration": 3600,
            "priority": "high",
            "status": "invalid_status",
        }

        serializer = TaskSerializer(data=data, partial=False)
        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)
