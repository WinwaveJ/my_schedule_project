from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
import os
import json
import zipfile
from datetime import datetime


class DataBackup(models.Model):
    BACKUP_TYPE_CHOICES = [
        ('FULL', '完整备份'),
        ('INCREMENTAL', '增量备份'),
        ('SELECTIVE', '选择性备份'),
    ]

    BACKUP_STATUS_CHOICES = [
        ('PENDING', '等待中'),
        ('IN_PROGRESS', '进行中'),
        ('COMPLETED', '已完成'),
        ('FAILED', '失败'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='data_backups')
    backup_type = models.CharField(max_length=20, choices=BACKUP_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=BACKUP_STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    file_path = models.CharField(max_length=255, null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    included_modules = models.JSONField(default=list)
    error_message = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'backup_type']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.backup_type} - {self.created_at}"

    def clean(self):
        if self.status == 'COMPLETED' and not self.file_path:
            raise ValidationError('完成状态的备份必须包含文件路径')
        if self.status == 'FAILED' and not self.error_message:
            raise ValidationError('失败状态的备份必须包含错误信息')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def get_file_size_display(self):
        if not self.file_size:
            return 'N/A'
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024:
                return f"{self.file_size:.2f} {unit}"
            self.file_size /= 1024
        return f"{self.file_size:.2f} TB"


class BackupSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('DAILY', '每天'),
        ('WEEKLY', '每周'),
        ('MONTHLY', '每月'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='backup_schedules')
    name = models.CharField(max_length=100)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    backup_type = models.CharField(max_length=20, choices=DataBackup.BACKUP_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    retention_days = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='备份保留天数'
    )
    included_modules = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['next_run']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    def clean(self):
        if not self.included_modules:
            raise ValidationError('必须选择至少一个要备份的模块')
        if self.retention_days < 1:
            raise ValidationError('备份保留天数必须大于0')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def calculate_next_run(self):
        from django.utils import timezone
        now = timezone.now()

        if self.frequency == 'DAILY':
            next_run = now.replace(hour=0, minute=0, second=0, microsecond=0) + timezone.timedelta(days=1)
        elif self.frequency == 'WEEKLY':
            next_run = now.replace(hour=0, minute=0, second=0, microsecond=0) + timezone.timedelta(days=7)
        elif self.frequency == 'MONTHLY':
            # 计算下个月的第一天
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month + 1, day=1)
            next_run = next_month.replace(hour=0, minute=0, second=0, microsecond=0)

        return next_run
