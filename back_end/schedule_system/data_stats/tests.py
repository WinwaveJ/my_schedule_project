from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import TaskStats, ActivityStats, EfficiencyStats
from .serializers import (
    TaskStatsSerializer,
    ActivityStatsSerializer,
    EfficiencyStatsSerializer
)
from datetime import timedelta, date

User = get_user_model()

class TaskStatsModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.task_stats = TaskStats.objects.create(
            user=self.user,
            date=date.today(),
            total_tasks=10,
            completed_tasks=5,
            overdue_tasks=2,
            priority_distribution={'high': 3, 'medium': 5, 'low': 2},
            completion_time_distribution={'morning': 2, 'afternoon': 2, 'evening': 1}
        )

    def test_task_stats_creation(self):
        """测试任务统计创建"""
        self.assertEqual(self.task_stats.total_tasks, 10)
        self.assertEqual(self.task_stats.completed_tasks, 5)
        self.assertEqual(self.task_stats.overdue_tasks, 2)
        self.assertEqual(self.task_stats.priority_distribution['high'], 3)

    def test_task_stats_str_representation(self):
        """测试任务统计的字符串表示"""
        expected_str = f"{self.user.username} - {date.today()}"
        self.assertEqual(str(self.task_stats), expected_str)

class ActivityStatsModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.activity_stats = ActivityStats.objects.create(
            user=self.user,
            date=date.today(),
            pomodoro_duration=timedelta(hours=2),
            stopwatch_duration=timedelta(hours=1),
            activity_type_distribution={'study': 2, 'work': 1},
            daily_trend={'morning': 2, 'afternoon': 1}
        )

    def test_activity_stats_creation(self):
        """测试活动统计创建"""
        self.assertEqual(self.activity_stats.pomodoro_duration, timedelta(hours=2))
        self.assertEqual(self.activity_stats.stopwatch_duration, timedelta(hours=1))
        self.assertEqual(self.activity_stats.activity_type_distribution['study'], 2)

class EfficiencyStatsModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.efficiency_stats = EfficiencyStats.objects.create(
            user=self.user,
            date=date.today(),
            efficiency_score=85.5,
            time_allocation={'productive': 70, 'neutral': 20, 'unproductive': 10},
            goal_achievement_rate=75.0,
            habit_tracking={'meditation': True, 'exercise': False}
        )

    def test_efficiency_stats_creation(self):
        """测试效率统计创建"""
        self.assertEqual(self.efficiency_stats.efficiency_score, 85.5)
        self.assertEqual(self.efficiency_stats.goal_achievement_rate, 75.0)
        self.assertTrue(self.efficiency_stats.habit_tracking['meditation'])

class StatsViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # 创建测试数据
        self.task_stats = TaskStats.objects.create(
            user=self.user,
            date=date.today(),
            total_tasks=10,
            completed_tasks=5,
            overdue_tasks=2,
            priority_distribution={'high': 3, 'medium': 5, 'low': 2},
            completion_time_distribution={'morning': 2, 'afternoon': 2, 'evening': 1}
        )
        
        self.activity_stats = ActivityStats.objects.create(
            user=self.user,
            date=date.today(),
            pomodoro_duration=timedelta(hours=2),
            stopwatch_duration=timedelta(hours=1),
            activity_type_distribution={'study': 2, 'work': 1},
            daily_trend={'morning': 2, 'afternoon': 1}
        )
        
        self.efficiency_stats = EfficiencyStats.objects.create(
            user=self.user,
            date=date.today(),
            efficiency_score=85.5,
            time_allocation={'productive': 70, 'neutral': 20, 'unproductive': 10},
            goal_achievement_rate=75.0,
            habit_tracking={'meditation': True, 'exercise': False}
        )

    def test_task_stats_list(self):
        """测试获取任务统计列表"""
        response = self.client.get('/api/task-stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_activity_stats_list(self):
        """测试获取活动统计列表"""
        response = self.client.get('/api/activity-stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_efficiency_stats_list(self):
        """测试获取效率统计列表"""
        response = self.client.get('/api/efficiency-stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_stats_summary(self):
        """测试获取统计汇总"""
        response = self.client.get('/api/stats/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('task_stats', response.data)
        self.assertIn('activity_stats', response.data)
        self.assertIn('efficiency_stats', response.data)

    def test_date_range_filter(self):
        """测试日期范围过滤"""
        # 创建不同日期的统计数据
        yesterday = date.today() - timedelta(days=1)
        tomorrow = date.today() + timedelta(days=1)
        
        TaskStats.objects.create(
            user=self.user,
            date=yesterday,
            total_tasks=5,
            completed_tasks=3,
            overdue_tasks=1,
            priority_distribution={'high': 2, 'medium': 2, 'low': 1},
            completion_time_distribution={'morning': 1, 'afternoon': 1, 'evening': 1}
        )
        
        TaskStats.objects.create(
            user=self.user,
            date=tomorrow,
            total_tasks=8,
            completed_tasks=4,
            overdue_tasks=2,
            priority_distribution={'high': 3, 'medium': 3, 'low': 2},
            completion_time_distribution={'morning': 2, 'afternoon': 1, 'evening': 1}
        )
        
        # 测试开始日期过滤
        response = self.client.get(f'/api/task-stats/?start_date={date.today()}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 今天和明天的数据
        
        # 测试结束日期过滤
        response = self.client.get(f'/api/task-stats/?end_date={date.today()}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 昨天和今天的数据
        
        # 测试日期范围过滤
        response = self.client.get(
            f'/api/task-stats/?start_date={yesterday}&end_date={date.today()}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 昨天和今天的数据

    def test_task_stats_summary(self):
        """测试任务统计摘要"""
        response = self.client.get('/api/task-stats/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_tasks', response.data)
        self.assertIn('completed_tasks', response.data)
        self.assertIn('overdue_tasks', response.data)
        self.assertIn('completion_rate', response.data)
        self.assertIn('overdue_rate', response.data)

    def test_activity_stats_summary(self):
        """测试活动统计摘要"""
        response = self.client.get('/api/activity-stats/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_pomodoro_duration', response.data)
        self.assertIn('total_stopwatch_duration', response.data)
        self.assertIn('total_duration', response.data)

    def test_efficiency_stats_summary(self):
        """测试效率统计摘要"""
        response = self.client.get('/api/efficiency-stats/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('average_efficiency_score', response.data)
        self.assertIn('average_goal_achievement_rate', response.data)

    def test_unauthorized_access(self):
        """测试未授权访问"""
        self.client.force_authenticate(user=None)
        
        # 测试访问任务统计
        response = self.client.get('/api/task-stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 测试访问活动统计
        response = self.client.get('/api/activity-stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 测试访问效率统计
        response = self.client.get('/api/efficiency-stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 测试访问统计汇总
        response = self.client.get('/api/stats/summary/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_other_user_data_access(self):
        """测试访问其他用户的数据"""
        # 创建另一个用户及其数据
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        other_task_stats = TaskStats.objects.create(
            user=other_user,
            date=date.today(),
            total_tasks=15,
            completed_tasks=7,
            overdue_tasks=3,
            priority_distribution={'high': 5, 'medium': 7, 'low': 3},
            completion_time_distribution={'morning': 3, 'afternoon': 2, 'evening': 2}
        )
        
        # 验证当前用户只能看到自己的数据
        response = self.client.get('/api/task-stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['total_tasks'], self.task_stats.total_tasks)
