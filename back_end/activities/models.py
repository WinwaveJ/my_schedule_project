from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.apps import apps
from users.models import User
from app_settings.models import AppSettings


class BaseActivity(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "未开始"),
        ("IN_PROGRESS", "进行中"),
        ("COMPLETED", "已完成"),
        ("PAUSED", "已暂停"),
        ("CANCELLED", "已取消"),
    ]

    title = models.CharField(max_length=200, verbose_name="活动标题")
    description = models.TextField(blank=True, null=True, verbose_name="活动描述")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="%(class)s_activities",
        verbose_name="所属用户",
    )
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        related_name="%(class)s_activities",
        verbose_name="关联任务",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        verbose_name="状态",
    )
    start_time = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    duration = models.DurationField(null=True, blank=True, verbose_name="持续时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        abstract = True
        verbose_name = "基础活动"
        verbose_name_plural = "基础活动"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def clean(self):
        if self.end_time and self.start_time and self.end_time < self.start_time:
            raise ValidationError("结束时间不能早于开始时间")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class PomodoroActivity(BaseActivity):
    """番茄钟活动"""
    pomodoro_count = models.IntegerField(
        default=0, validators=[MinValueValidator(0)], verbose_name="已完成番茄钟数"
    )
    current_pomodoro_start = models.DateTimeField(
        null=True, blank=True, verbose_name="当前番茄钟开始时间"
    )
    current_break_start = models.DateTimeField(
        null=True, blank=True, verbose_name="当前休息开始时间"
    )
    is_break = models.BooleanField(default=False, verbose_name="是否处于休息状态")
    is_long_break = models.BooleanField(
        default=False, verbose_name="是否处于长休息状态"
    )

    class Meta:
        verbose_name = "番茄钟活动"
        verbose_name_plural = "番茄钟活动"
        ordering = ["-created_at"]

    def start_pomodoro(self):
        """开始一个新的番茄钟"""
        settings = AppSettings.objects.get(user=self.user)
        self.current_pomodoro_start = timezone.now()
        self.is_break = False
        self.is_long_break = False
        self.status = "IN_PROGRESS"
        self.save()

    def start_break(self, is_long_break=False):
        """开始休息"""
        if not self.current_pomodoro_start:
            raise ValidationError("必须先开始番茄钟才能开始休息")

        settings = AppSettings.objects.get(user=self.user)
        self.current_break_start = timezone.now()
        self.is_break = True
        self.is_long_break = is_long_break
        self.save()

    def complete_pomodoro(self):
        """完成一个番茄钟"""
        if not self.current_pomodoro_start:
            raise ValidationError("没有正在进行的番茄钟")

        self.pomodoro_count += 1
        self.current_pomodoro_start = None
        self.current_break_start = None
        self.is_break = False
        self.is_long_break = False
        self.status = "COMPLETED"
        self.save()

    def __str__(self):
        return f"{self.title} - {self.pomodoro_count}个番茄钟"


class StopwatchActivity(BaseActivity):
    """正计时活动"""
    start_time = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="结束时间")
    duration = models.DurationField(null=True, blank=True, verbose_name="活动时长")

    class Meta:
        verbose_name = "正计时活动"
        verbose_name_plural = "正计时活动"
        ordering = ["-created_at"]

    def start_stopwatch(self):
        """开始正计时"""
        self.start_time = timezone.now()
        self.status = "IN_PROGRESS"
        self.save()

    def stop_stopwatch(self):
        """停止正计时"""
        if not self.start_time:
            raise ValidationError("没有正在进行的计时")

        self.end_time = timezone.now()
        self.duration = self.end_time - self.start_time
        self.status = "COMPLETED"
        self.save()

    def get_remaining_time(self):
        """获取剩余时间"""
        if self.timer_type == "POMODORO":
            settings = AppSettings.objects.get(user=self.user)
            if self.is_break:
                if self.is_long_break:
                    total_break_time = settings.long_break_duration
                else:
                    total_break_time = settings.short_break_duration
                if self.current_break_start:
                    elapsed = timezone.now() - self.current_break_start
                    return max(total_break_time - elapsed, timezone.timedelta())
            else:
                total_pomodoro_time = settings.pomodoro_duration
                if self.current_pomodoro_start:
                    elapsed = timezone.now() - self.current_pomodoro_start
                    return max(total_pomodoro_time - elapsed, timezone.timedelta())
        return None

    def get_elapsed_time(self):
        """获取已用时间"""
        if self.timer_type == "STOPWATCH" and self.start_time:
            return timezone.now() - self.start_time
        return None

    def __str__(self):
        return f"{self.title} - {self.duration}"
