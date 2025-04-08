from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import DataBackup, BackupSchedule
from .serializers import (
    DataBackupSerializer,
    BackupScheduleSerializer,
    BackupScheduleDetailSerializer
)


class DataBackupViewSet(viewsets.ModelViewSet):
    serializer_class = DataBackupSerializer
    permission_classes = [IsAuthenticated]
    queryset = DataBackup.objects.all()

    def get_queryset(self):
        queryset = DataBackup.objects.filter(user=self.request.user)

        # 按备份类型筛选
        backup_type = self.request.query_params.get('backup_type', None)
        if backup_type:
            queryset = queryset.filter(backup_type=backup_type)

        # 按状态筛选
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)

        # 按时间范围筛选
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """
        从备份恢复数据
        """
        backup = self.get_object()
        if backup.status != 'COMPLETED':
            return Response(
                {'error': '只能从已完成的备份恢复数据'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # TODO: 实现数据恢复逻辑
            return Response({'message': '数据恢复已开始'})
        except Exception as e:
            return Response(
                {'error': f'数据恢复失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def create_backup(self, request):
        """
        创建新的备份
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        try:
            # TODO: 实现异步备份逻辑
            return Response(
                {'message': '备份任务已创建'},
                status=status.HTTP_202_ACCEPTED
            )
        except Exception as e:
            return Response(
                {'error': f'创建备份失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BackupScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = BackupScheduleSerializer
    permission_classes = [IsAuthenticated]
    queryset = BackupSchedule.objects.all()

    def get_queryset(self):
        queryset = BackupSchedule.objects.filter(user=self.request.user)

        # 按是否激活筛选
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # 按备份类型筛选
        backup_type = self.request.query_params.get('backup_type', None)
        if backup_type:
            queryset = queryset.filter(backup_type=backup_type)

        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BackupScheduleDetailSerializer
        return BackupScheduleSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        切换备份计划的激活状态
        """
        schedule = self.get_object()
        schedule.is_active = not schedule.is_active
        schedule.save()
        return Response({'is_active': schedule.is_active})

    @action(detail=True, methods=['post'])
    def run_now(self, request, pk=None):
        """
        立即执行备份计划
        """
        schedule = self.get_object()
        try:
            # TODO: 实现立即执行备份的逻辑
            return Response({'message': '备份任务已创建'})
        except Exception as e:
            return Response(
                {'error': f'执行备份失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
