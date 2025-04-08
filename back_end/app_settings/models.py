from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from users.models import User
from django.conf import settings


class TaskCategory(models.Model):
    name = models.CharField(max_length=50, verbose_name="分类名称")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_categories",
        verbose_name="所属用户",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "任务分类"
        verbose_name_plural = "任务分类"
        unique_together = ["name", "user"]
        ordering = ["name"]

    def __str__(self):
        return self.name


class AppSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="app_settings",
        verbose_name="用户",
    )

    # 番茄钟设置
    pomodoro_duration = models.IntegerField(
        default=25,
        verbose_name="番茄钟时长（分钟）",
        help_text="单个番茄钟的持续时间",
    )
    short_break_duration = models.IntegerField(
        default=5,
        verbose_name="短休息时长（分钟）",
        help_text="完成一个番茄钟后的短休息时间",
    )
    long_break_duration = models.IntegerField(
        default=15,
        verbose_name="长休息时长（分钟）",
        help_text="完成多个番茄钟后的长休息时间",
    )
    long_break_interval = models.IntegerField(
        default=4,
        verbose_name="长休息间隔",
        help_text="多少个番茄钟后进行一次长休息",
    )

    # 其他设置
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "应用设置"
        verbose_name_plural = "应用设置"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} 的应用设置"

    def save(self, *args, **kwargs):
        # 确保时长设置合理
        if self.pomodoro_duration <= 0:
            raise ValueError("番茄钟时长必须大于0")
        if self.short_break_duration <= 0:
            raise ValueError("短休息时长必须大于0")
        if self.long_break_duration <= 0:
            raise ValueError("长休息时长必须大于0")
        super().save(*args, **kwargs)
