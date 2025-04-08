from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import DataBackup, BackupSchedule
from .serializers import (
    DataBackupSerializer,
    BackupScheduleSerializer,
    BackupScheduleDetailSerializer
)
from datetime import timedelta
from django.core.exceptions import ValidationError

User = get_user_model()

class DataBackupModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.backup = DataBackup.objects.create(
            user=self.user,
            backup_type='FULL',
            status='COMPLETED',
            file_path='/path/to/backup.zip',
            file_size=1024 * 1024,  # 1MB
            included_modules=['tasks', 'activities'],
            metadata={'version': '1.0'}
        )

    def test_backup_creation(self):
        """测试备份创建"""
        self.assertEqual(self.backup.backup_type, 'FULL')
        self.assertEqual(self.backup.status, 'COMPLETED')
        self.assertEqual(self.backup.file_size, 1024 * 1024)
        self.assertEqual(len(self.backup.included_modules), 2)

    def test_backup_str_representation(self):
        """测试备份的字符串表示"""
        expected_str = f"{self.user.username} - FULL - {self.backup.created_at}"
        self.assertEqual(str(self.backup), expected_str)

    def test_file_size_display(self):
        """测试文件大小显示"""
        self.assertEqual(self.backup.get_file_size_display(), '1.00 MB')

    def test_backup_validation(self):
        """测试备份验证"""
        # 测试完成状态但没有文件路径的情况
        with self.assertRaises(ValidationError):
            backup = DataBackup(
                user=self.user,
                backup_type='FULL',
                status='COMPLETED',
                file_path=None
            )
            backup.clean()

        # 测试失败状态但没有错误信息的情况
        with self.assertRaises(ValidationError):
            backup = DataBackup(
                user=self.user,
                backup_type='FULL',
                status='FAILED',
                error_message=None
            )
            backup.clean()

    def test_backup_status_transitions(self):
        """测试备份状态转换"""
        backup = DataBackup.objects.create(
            user=self.user,
            backup_type='FULL',
            status='PENDING'
        )
        
        # 测试状态转换
        backup.status = 'IN_PROGRESS'
        backup.save()
        self.assertEqual(backup.status, 'IN_PROGRESS')
        
        backup.status = 'COMPLETED'
        backup.file_path = '/path/to/backup.zip'
        backup.save()
        self.assertEqual(backup.status, 'COMPLETED')
        
        backup.status = 'FAILED'
        backup.error_message = '备份失败'
        backup.save()
        self.assertEqual(backup.status, 'FAILED')

    def test_backup_file_size_conversion(self):
        """测试文件大小单位转换"""
        # 测试不同大小的文件显示
        sizes = [
            (1024, '1.00 KB'),
            (1024 * 1024, '1.00 MB'),
            (1024 * 1024 * 1024, '1.00 GB'),
            (1024 * 1024 * 1024 * 1024, '1.00 TB')
        ]
        
        for size, expected in sizes:
            backup = DataBackup.objects.create(
                user=self.user,
                backup_type='FULL',
                status='COMPLETED',
                file_path='/path/to/backup.zip',
                file_size=size
            )
            self.assertEqual(backup.get_file_size_display(), expected)

class BackupScheduleModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.schedule = BackupSchedule.objects.create(
            user=self.user,
            name='每日备份',
            frequency='DAILY',
            backup_type='FULL',
            retention_days=7,
            included_modules=['tasks', 'activities']
        )

    def test_schedule_creation(self):
        """测试备份计划创建"""
        self.assertEqual(self.schedule.name, '每日备份')
        self.assertEqual(self.schedule.frequency, 'DAILY')
        self.assertEqual(self.schedule.backup_type, 'FULL')
        self.assertEqual(self.schedule.retention_days, 7)
        self.assertTrue(self.schedule.is_active)

    def test_schedule_validation(self):
        """测试备份计划验证"""
        with self.assertRaises(Exception):
            BackupSchedule.objects.create(
                user=self.user,
                name='无效备份',
                frequency='DAILY',
                backup_type='FULL',
                retention_days=7,
                included_modules=[]  # 空模块列表应该触发验证错误
            )

    def test_schedule_next_run_calculation(self):
        """测试下次运行时间计算"""
        now = timezone.now()
        
        # 测试每日备份
        daily_schedule = BackupSchedule.objects.create(
            user=self.user,
            name='每日备份',
            frequency='DAILY',
            backup_type='FULL',
            retention_days=7,
            included_modules=['tasks']
        )
        next_run = daily_schedule.calculate_next_run()
        expected_daily = (now.replace(hour=0, minute=0, second=0, microsecond=0) + 
                         timezone.timedelta(days=1))
        self.assertEqual(next_run.date(), expected_daily.date())
        
        # 测试每周备份
        weekly_schedule = BackupSchedule.objects.create(
            user=self.user,
            name='每周备份',
            frequency='WEEKLY',
            backup_type='FULL',
            retention_days=7,
            included_modules=['tasks']
        )
        next_run = weekly_schedule.calculate_next_run()
        expected_weekly = (now.replace(hour=0, minute=0, second=0, microsecond=0) + 
                          timezone.timedelta(days=7))
        self.assertEqual(next_run.date(), expected_weekly.date())
        
        # 测试每月备份
        monthly_schedule = BackupSchedule.objects.create(
            user=self.user,
            name='每月备份',
            frequency='MONTHLY',
            backup_type='FULL',
            retention_days=7,
            included_modules=['tasks']
        )
        next_run = monthly_schedule.calculate_next_run()
        if now.month == 12:
            expected_monthly = now.replace(year=now.year + 1, month=1, day=1)
        else:
            expected_monthly = now.replace(month=now.month + 1, day=1)
        expected_monthly = expected_monthly.replace(hour=0, minute=0, second=0, microsecond=0)
        self.assertEqual(next_run.date(), expected_monthly.date())

    def test_schedule_retention_days_validation(self):
        """测试保留天数验证"""
        with self.assertRaises(ValidationError):
            BackupSchedule.objects.create(
                user=self.user,
                name='无效保留天数',
                frequency='DAILY',
                backup_type='FULL',
                retention_days=0,  # 应该触发验证错误
                included_modules=['tasks']
            )

    def test_schedule_status_updates(self):
        """测试备份计划状态更新"""
        # 测试最后运行时间更新
        self.schedule.last_run = timezone.now()
        self.schedule.save()
        self.assertIsNotNone(self.schedule.last_run)
        
        # 测试下次运行时间更新
        self.schedule.next_run = timezone.now() + timezone.timedelta(days=1)
        self.schedule.save()
        self.assertIsNotNone(self.schedule.next_run)
        
        # 测试激活状态切换
        self.schedule.is_active = False
        self.schedule.save()
        self.assertFalse(self.schedule.is_active)

class BackupViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # 创建测试数据
        self.backup = DataBackup.objects.create(
            user=self.user,
            backup_type='FULL',
            status='COMPLETED',
            file_path='/path/to/backup.zip',
            file_size=1024 * 1024,
            included_modules=['tasks', 'activities'],
            metadata={'version': '1.0'}
        )
        
        self.schedule = BackupSchedule.objects.create(
            user=self.user,
            name='每日备份',
            frequency='DAILY',
            backup_type='FULL',
            retention_days=7,
            included_modules=['tasks']
        )

    def test_list_backups(self):
        """测试获取备份列表"""
        response = self.client.get('/api/backups/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_backup(self):
        """测试创建备份"""
        data = {
            'backup_type': 'FULL',
            'included_modules': ['tasks', 'activities'],
            'metadata': {'version': '1.0'}
        }
        response = self.client.post('/api/backups/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_restore_backup(self):
        """测试恢复备份"""
        response = self.client.post(f'/api/backups/{self.backup.id}/restore/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_backup_filtering(self):
        """测试备份筛选功能"""
        # 创建多个备份用于测试筛选
        DataBackup.objects.create(
            user=self.user,
            backup_type='INCREMENTAL',
            status='COMPLETED',
            file_path='/path/to/backup2.zip',
            file_size=512 * 1024,
            included_modules=['tasks']
        )
        
        # 测试按备份类型筛选
        response = self.client.get('/api/backups/?backup_type=FULL')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # 测试按状态筛选
        response = self.client.get('/api/backups/?status=COMPLETED')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_backup_restore_validation(self):
        """测试备份恢复验证"""
        # 创建一个未完成的备份
        incomplete_backup = DataBackup.objects.create(
            user=self.user,
            backup_type='FULL',
            status='IN_PROGRESS',
            included_modules=['tasks']
        )
        
        # 尝试恢复未完成的备份
        response = self.client.post(f'/api/backups/{incomplete_backup.id}/restore/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class BackupScheduleViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.schedule = BackupSchedule.objects.create(
            user=self.user,
            name='每日备份',
            frequency='DAILY',
            backup_type='FULL',
            retention_days=7,
            included_modules=['tasks']
        )

    def test_list_schedules(self):
        """测试获取备份计划列表"""
        response = self.client.get('/api/schedules/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_schedule(self):
        """测试创建备份计划"""
        data = {
            'name': '每周备份',
            'frequency': 'WEEKLY',
            'backup_type': 'FULL',
            'retention_days': 30,
            'included_modules': ['tasks', 'activities'],
            'is_active': True
        }
        response = self.client.post('/api/schedules/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_toggle_schedule_active(self):
        """测试切换备份计划激活状态"""
        response = self.client.post(f'/api/schedules/{self.schedule.id}/toggle_active/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_run_schedule_now(self):
        """测试立即执行备份计划"""
        response = self.client.post(f'/api/schedules/{self.schedule.id}/run_now/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_schedule_filtering(self):
        """测试备份计划筛选功能"""
        # 创建多个备份计划用于测试筛选
        BackupSchedule.objects.create(
            user=self.user,
            name='每月备份',
            frequency='MONTHLY',
            backup_type='INCREMENTAL',
            retention_days=90,
            included_modules=['tasks'],
            is_active=False
        )
        
        # 测试按激活状态筛选
        response = self.client.get('/api/schedules/?is_active=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # 测试按备份类型筛选
        response = self.client.get('/api/schedules/?backup_type=FULL')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_schedule_validation(self):
        """测试备份计划验证"""
        # 尝试创建无效的备份计划
        data = {
            'name': '无效备份',
            'frequency': 'DAILY',
            'backup_type': 'FULL',
            'retention_days': 0,  # 无效的保留天数
            'included_modules': ['tasks']
        }
        response = self.client.post('/api/schedules/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_schedule_detail(self):
        """测试备份计划详情"""
        response = self.client.get(f'/api/schedules/{self.schedule.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '每日备份')
