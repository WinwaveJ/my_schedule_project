from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.apps import apps
from users.models import User
from app_settings.models import TaskCategory
from activities.models import PomodoroActivity, StopwatchActivity


class Task(models.Model):
    PRIORITY_CHOICES = [
        ("URGENT_IMPORTANT", "紧急重要"),
        ("NOT_URGENT_IMPORTANT", "重要不紧急"),
        ("URGENT_NOT_IMPORTANT", "紧急不重要"),
        ("NOT_URGENT_NOT_IMPORTANT", "不重要不紧急"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "未开始"),
        ("IN_PROGRESS", "进行中"),
        ("COMPLETED", "已完成"),
        ("OVERDUE", "已逾期"),
    ]

    title = models.CharField(max_length=200, verbose_name="任务标题")
    description = models.TextField(blank=True, null=True, verbose_name="任务描述")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="所属用户",
    )
    category = models.ForeignKey(
        TaskCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="任务分类",
    )
    priority = models.CharField(
        max_length=25,
        choices=PRIORITY_CHOICES,
        default="NOT_URGENT_NOT_IMPORTANT",
        verbose_name="优先级",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        verbose_name="状态",
    )
    due_date = models.DateTimeField(verbose_name="截止时间")
    estimated_duration = models.DurationField(
        null=True, blank=True, verbose_name="预计时长"
    )
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="进度",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "任务"
        verbose_name_plural = "任务"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def clean(self):
        # 只在创建新任务时验证截止时间
        if not self.pk and self.due_date < timezone.now():
            raise ValidationError("截止时间不能早于当前时间")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def focused_duration(self):
        """获取任务的实际专注时长（分钟）"""
        PomodoroActivity = apps.get_model('activities', 'PomodoroActivity')
        StopwatchActivity = apps.get_model('activities', 'StopwatchActivity')
        
        pomodoro_activities = PomodoroActivity.objects.filter(
            task=self, status="COMPLETED"
        )
        stopwatch_activities = StopwatchActivity.objects.filter(
            task=self, status="COMPLETED"
        )
        
        total_minutes = 0
        
        # 计算番茄钟时长
        for activity in pomodoro_activities:
            total_minutes += activity.pomodoro_count * 25  # 每个番茄钟25分钟
            
        # 计算正计时时长
        for activity in stopwatch_activities:
            if activity.duration:
                total_minutes += activity.duration.total_seconds() / 60
                
        return round(total_minutes)
