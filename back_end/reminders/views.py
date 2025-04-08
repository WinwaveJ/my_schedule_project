from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import Reminder
from .serializers import ReminderSerializer


class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Reminder.objects.filter(user=self.request.user)

        # 按提醒类型筛选
        reminder_type = self.request.query_params.get('reminder_type', None)
        if reminder_type:
            queryset = queryset.filter(reminder_type=reminder_type)

        # 按提醒方式筛选
        reminder_method = self.request.query_params.get('reminder_method', None)
        if reminder_method:
            queryset = queryset.filter(reminder_method=reminder_method)

        # 按关联任务筛选
        task_id = self.request.query_params.get('task_id', None)
        if task_id:
            queryset = queryset.filter(related_task_id=task_id)

        # 按关联活动筛选
        activity_id = self.request.query_params.get('activity_id', None)
        if activity_id:
            queryset = queryset.filter(related_activity_id=activity_id)

        # 按时间范围筛选
        start_time = self.request.query_params.get('start_time', None)
        end_time = self.request.query_params.get('end_time', None)
        if start_time:
            try:
                start_time = timezone.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                queryset = queryset.filter(reminder_time__gte=start_time)
            except ValueError:
                pass
        if end_time:
            try:
                end_time = timezone.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                queryset = queryset.filter(reminder_time__lte=end_time)
            except ValueError:
                pass

        # 按标题搜索
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        获取即将到来的提醒
        """
        now = timezone.now()
        queryset = self.get_queryset().filter(
            reminder_time__gte=now,
            is_active=True
        ).order_by('reminder_time')[:10]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """
        切换提醒的激活状态
        """
        reminder = self.get_object()
        reminder.is_active = not reminder.is_active
        reminder.save()
        serializer = self.get_serializer(reminder)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        """批量删除提醒"""
        reminder_ids = request.data.get('reminder_ids', [])
        if not reminder_ids:
            return Response(
                {'detail': '请提供要删除的提醒ID列表'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 只删除当前用户的提醒
        deleted_count = Reminder.objects.filter(
            user=request.user,
            id__in=reminder_ids
        ).delete()[0]
        
        if deleted_count == 0:
            return Response(
                {'detail': '没有找到要删除的提醒'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """
        批量更新提醒
        """
        reminder_updates = request.data.get('reminder_updates', [])
        if not reminder_updates:
            return Response(
                {'error': '请提供要更新的提醒数据'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(reminder_updates, list):
            return Response(
                {'error': 'reminder_updates 必须是列表'},
                status=status.HTTP_400_BAD_REQUEST
            )

        updated_count = 0
        errors = []

        for update in reminder_updates:
            if not isinstance(update, dict):
                errors.append({
                    'error': '更新数据必须是字典格式',
                    'data': str(update)
                })
                continue

            reminder_id = update.get('id')
            if not reminder_id:
                errors.append({
                    'error': '缺少提醒ID',
                    'data': str(update)
                })
                continue

            reminder = self.get_queryset().filter(id=reminder_id).first()
            if not reminder:
                errors.append({
                    'error': f'找不到ID为{reminder_id}的提醒',
                    'data': str(update)
                })
                continue

            serializer = self.get_serializer(reminder, data=update, partial=True)
            try:
                if serializer.is_valid():
                    serializer.save()
                    updated_count += 1
                else:
                    errors.append({
                        'id': reminder_id,
                        'errors': serializer.errors,
                        'data': str(update),
                        'validation_data': serializer.validated_data
                    })
            except Exception as e:
                errors.append({
                    'id': reminder_id,
                    'error': str(e),
                    'data': str(update),
                    'exception_type': type(e).__name__
                })

        response_data = {
            'message': f'成功更新 {updated_count} 个提醒',
            'errors': errors if errors else None,
            'request_data': request.data
        }

        # 如果有任何更新成功，就返回 200
        if updated_count > 0:
            return Response(response_data)
        
        # 如果所有更新都失败，返回 400
        if errors:
            response_data['error'] = '所有更新都失败了'
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        
        # 如果没有任何更新操作，返回 400
        return Response({
            'error': '没有可更新的数据'
        }, status=status.HTTP_400_BAD_REQUEST)
