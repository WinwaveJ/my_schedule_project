from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from django.db.models.functions import TruncDate
from django.db.models import Count, Sum, Avg
from tasks.models import Task
from .models import ActivityStats, EfficiencyStats
from .serializers import (
    TaskStatsSerializer,
    ActivityStatsSerializer,
    EfficiencyStatsSerializer,
    StatsSummarySerializer
)


class TaskStatsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TaskStatsSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        获取任务统计摘要
        """
        user = request.user
        today = timezone.now().date()
        
        # 获取所有任务
        all_tasks = Task.objects.filter(user=user)
        
        # 获取已完成任务
        completed_tasks = all_tasks.filter(status='COMPLETED')
        
        # 获取逾期任务（状态为OVERDUE或状态为pending且截止日期小于今天）
        overdue_tasks = all_tasks.filter(
            Q(status='OVERDUE') |
            (Q(status='PENDING') & Q(due_date__lt=today))
        )
        
        # 获取今日任务
        today_tasks = all_tasks.filter(
            Q(created_at__date=today) | 
            Q(due_date__date=today)
        )
        
        # 获取今日已完成任务
        today_completed = today_tasks.filter(status='COMPLETED')
        
        # 计算统计数据
        total_tasks = all_tasks.count()
        completed_count = completed_tasks.count()
        today_total = today_tasks.count()
        today_completed_count = today_completed.count()
        overdue_count = overdue_tasks.count()
        
        # 计算完成率
        completion_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        today_completion_rate = (today_completed_count / today_total * 100) if today_total > 0 else 0
        overdue_rate = (overdue_count / total_tasks * 100) if total_tasks > 0 else 0

        return Response({
            'total_tasks': total_tasks,
            'completed_tasks': completed_count,
            'overdue_tasks': overdue_count,
            'completion_rate': completion_rate,
            'overdue_rate': overdue_rate,
            'today_total': today_total,
            'today_completed': today_completed_count,
            'today_completion_rate': today_completion_rate
        })


class ActivityStatsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivityStatsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = ActivityStats.objects.filter(user=self.request.user)

        # 按日期范围筛选
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        获取活动统计摘要
        """
        queryset = self.get_queryset()
        total_pomodoro = queryset.aggregate(total=Sum('pomodoro_duration'))['total'] or 0
        total_stopwatch = queryset.aggregate(total=Sum('stopwatch_duration'))['total'] or 0

        return Response({
            'total_pomodoro_duration': total_pomodoro,
            'total_stopwatch_duration': total_stopwatch,
            'total_duration': total_pomodoro + total_stopwatch
        })


class EfficiencyStatsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EfficiencyStatsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = EfficiencyStats.objects.filter(user=self.request.user)

        # 按日期范围筛选
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        获取效率统计摘要
        """
        queryset = self.get_queryset()
        avg_efficiency = queryset.aggregate(avg=Avg('efficiency_score'))['avg'] or 0
        avg_goal_achievement = queryset.aggregate(avg=Avg('goal_achievement_rate'))['avg'] or 0

        return Response({
            'average_efficiency_score': avg_efficiency,
            'average_goal_achievement_rate': avg_goal_achievement
        })


class StatsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        获取所有统计数据的汇总
        """
        user = request.user
        today = timezone.now().date()
        
        # 获取任务统计
        all_tasks = Task.objects.filter(user=user)
        today_tasks = all_tasks.filter(
            Q(created_at__date=today) | 
            Q(due_date__date=today)
        )
        completed_tasks = all_tasks.filter(status='COMPLETED')
        today_completed = today_tasks.filter(status='COMPLETED')
        overdue_tasks = all_tasks.filter(
            Q(status='OVERDUE') |
            (Q(status='PENDING') & Q(due_date__lt=today))
        )
        
        # 计算任务统计数据
        total_tasks = all_tasks.count()
        completed_count = completed_tasks.count()
        today_total = today_tasks.count()
        today_completed_count = today_completed.count()
        overdue_count = overdue_tasks.count()
        
        # 计算完成率
        completion_rate = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        today_completion_rate = (today_completed_count / today_total * 100) if today_total > 0 else 0
        overdue_rate = (overdue_count / total_tasks * 100) if total_tasks > 0 else 0

        # 获取活动统计
        activity_stats = ActivityStats.objects.filter(user=user)
        total_pomodoro = activity_stats.aggregate(total=Sum('pomodoro_duration'))['total'] or 0
        total_stopwatch = activity_stats.aggregate(total=Sum('stopwatch_duration'))['total'] or 0

        # 获取最近7天的活动统计
        daily_stats = []
        for i in range(6, -1, -1):
            date = today - timezone.timedelta(days=i)
            stats = activity_stats.filter(date=date).first()
            daily_stats.append({
                'date': date,
                'pomodoro_duration': stats.pomodoro_duration.total_seconds() / 60 if stats else 0,
                'stopwatch_duration': stats.stopwatch_duration.total_seconds() / 60 if stats else 0
            })

        # 获取效率统计
        efficiency_stats = EfficiencyStats.objects.filter(user=user)
        avg_efficiency = efficiency_stats.aggregate(avg=Avg('efficiency_score'))['avg'] or 0
        avg_goal_achievement = efficiency_stats.aggregate(avg=Avg('goal_achievement_rate'))['avg'] or 0

        data = {
            'task_stats': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_count,
                'overdue_tasks': overdue_count,
                'completion_rate': completion_rate,
                'overdue_rate': overdue_rate,
                'today_total': today_total,
                'today_completed': today_completed_count,
                'today_completion_rate': today_completion_rate
            },
            'activity_stats': {
                'total_pomodoro_duration': total_pomodoro,
                'total_stopwatch_duration': total_stopwatch,
                'total_duration': total_pomodoro + total_stopwatch,
                'daily_pomodoro_duration': [stat['pomodoro_duration'] for stat in daily_stats],
                'daily_stopwatch_duration': [stat['stopwatch_duration'] for stat in daily_stats]
            },
            'efficiency_stats': {
                'average_efficiency_score': avg_efficiency,
                'average_goal_achievement_rate': avg_goal_achievement
            }
        }

        return Response(data)
