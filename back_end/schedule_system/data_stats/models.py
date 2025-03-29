from django.db import models
from users.models import User


class TaskStats(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_stats')
    date = models.DateField(verbose_name='统计日期')
    total_tasks = models.IntegerField(default=0, verbose_name='总任务数')
    completed_tasks = models.IntegerField(default=0, verbose_name='已完成任务数')
    overdue_tasks = models.IntegerField(default=0, verbose_name='逾期任务数')
    priority_distribution = models.JSONField(verbose_name='优先级分布')
    completion_time_distribution = models.JSONField(verbose_name='完成时间分布')

    class Meta:
        verbose_name = '任务统计'
        verbose_name_plural = '任务统计'
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class ActivityStats(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_stats')
    date = models.DateField(verbose_name='统计日期')
    pomodoro_duration = models.DurationField(default=0, verbose_name='番茄钟时长')
    stopwatch_duration = models.DurationField(default=0, verbose_name='正计时时长')
    activity_type_distribution = models.JSONField(verbose_name='活动类型分布')
    daily_trend = models.JSONField(verbose_name='每日活动趋势')

    class Meta:
        verbose_name = '活动统计'
        verbose_name_plural = '活动统计'
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class EfficiencyStats(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='efficiency_stats')
    date = models.DateField(verbose_name='统计日期')
    efficiency_score = models.FloatField(verbose_name='工作效率评分')
    time_allocation = models.JSONField(verbose_name='时间分配分析')
    goal_achievement_rate = models.FloatField(verbose_name='目标达成率')
    habit_tracking = models.JSONField(verbose_name='习惯养成追踪')

    class Meta:
        verbose_name = '效率统计'
        verbose_name_plural = '效率统计'
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date}"
