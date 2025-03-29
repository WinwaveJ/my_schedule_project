from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import PomodoroActivity, StopwatchActivity
from .serializers import PomodoroActivitySerializer, StopwatchActivitySerializer

# Create your views here.


class PomodoroActivityViewSet(viewsets.ModelViewSet):
    serializer_class = PomodoroActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = PomodoroActivity.objects.filter(user=self.request.user)

        # 按任务筛选
        task_id = self.request.query_params.get("task_id", None)
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        # 按状态筛选
        status = self.request.query_params.get("status", None)
        if status:
            queryset = queryset.filter(status=status)

        # 按创建时间筛选
        created_after = self.request.query_params.get("created_after", None)
        created_before = self.request.query_params.get("created_before", None)
        if created_after:
            queryset = queryset.filter(created_at__gte=created_after)
        if created_before:
            queryset = queryset.filter(created_at__lte=created_before)

        # 按标题模糊匹配
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return queryset

    @action(detail=True, methods=["post"])
    def start_pomodoro(self, request, pk=None):
        activity = self.get_object()
        try:
            activity.start_pomodoro()
            return Response({"status": "success"})
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def start_break(self, request, pk=None):
        activity = self.get_object()
        is_long_break = request.data.get("is_long_break", False)
        try:
            activity.start_break(is_long_break)
            return Response({"status": "success"})
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def complete_pomodoro(self, request, pk=None):
        activity = self.get_object()
        try:
            activity.complete_pomodoro()
            return Response({"status": "success"})
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StopwatchActivityViewSet(viewsets.ModelViewSet):
    serializer_class = StopwatchActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = StopwatchActivity.objects.filter(user=self.request.user)

        # 按任务筛选
        task_id = self.request.query_params.get("task_id", None)
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        # 按状态筛选
        status = self.request.query_params.get("status", None)
        if status:
            queryset = queryset.filter(status=status)

        # 按创建时间筛选
        created_after = self.request.query_params.get("created_after", None)
        created_before = self.request.query_params.get("created_before", None)
        if created_after:
            queryset = queryset.filter(created_at__gte=created_after)
        if created_before:
            queryset = queryset.filter(created_at__lte=created_before)

        # 按标题模糊匹配
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return queryset

    @action(detail=True, methods=["post"])
    def start_stopwatch(self, request, pk=None):
        activity = self.get_object()
        try:
            activity.start_stopwatch()
            return Response({"status": "success"})
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def stop_stopwatch(self, request, pk=None):
        activity = self.get_object()
        try:
            activity.stop_stopwatch()
            return Response({"status": "success"})
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        activity_ids = request.data.get("activity_ids", [])
        if not activity_ids:
            return Response(
                {"error": "请提供要删除的活动ID列表"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            StopwatchActivity.objects.filter(id__in=activity_ids, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def bulk_update(self, request):
        activity_updates = request.data.get("activity_updates", [])
        if not activity_updates:
            return Response(
                {"error": "请提供要更新的活动数据"}, status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            for update in activity_updates:
                activity_id = update.get("id")
                if not activity_id:
                    continue

                activity = StopwatchActivity.objects.filter(
                    id=activity_id, user=request.user
                ).first()

                if activity:
                    serializer = self.get_serializer(
                        activity, data=update, partial=True
                    )
                    if serializer.is_valid():
                        serializer.save()

        return Response({"message": "批量更新完成"})
