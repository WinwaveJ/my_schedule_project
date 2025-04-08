from django.db import models
from django.utils import timezone
from users.models import User
from tasks.models import Task
from activities.models import PomodoroActivity, StopwatchActivity
from django.core.exceptions import ValidationError


class Reminder(models.Model):
    REMINDER_TYPE_CHOICES = [
        ("TASK", "任务提醒"),
        ("ACTIVITY", "活动提醒"),
    ]

    title = models.CharField(max_length=200, verbose_name="提醒标题")
    description = models.TextField(blank=True, null=True, verbose_name="提醒描述")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reminders",
        verbose_name="所属用户",
    )
    reminder_type = models.CharField(
        max_length=20,
        choices=REMINDER_TYPE_CHOICES,
        default="TASK",
        verbose_name="提醒类型",
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="reminders",
        verbose_name="关联任务",
        null=True,
        blank=True,
    )
    pomodoro_activity = models.ForeignKey(
        PomodoroActivity,
        on_delete=models.CASCADE,
        related_name="reminders",
        verbose_name="关联番茄钟活动",
        null=True,
        blank=True,
    )
    stopwatch_activity = models.ForeignKey(
        StopwatchActivity,
        on_delete=models.CASCADE,
        related_name="reminders",
        verbose_name="关联正计时活动",
        null=True,
        blank=True,
    )
    remind_at = models.DateTimeField(verbose_name="提醒时间")
    is_read = models.BooleanField(default=False, verbose_name="是否已读")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "提醒"
        verbose_name_plural = "提醒"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def clean(self):
        if self.reminder_type == "TASK" and not self.task:
            raise ValidationError("任务提醒必须关联任务")
        elif self.reminder_type == "ACTIVITY" and not (self.pomodoro_activity or self.stopwatch_activity):
            raise ValidationError("活动提醒必须关联活动")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
