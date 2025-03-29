from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from django.db import transaction
from .models import Task, TaskTag
from .serializers import TaskSerializer, TaskTagSerializer

# Create your views here.


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Task.objects.filter(user=self.request.user)

        # 按标签筛选
        tag_ids = self.request.query_params.get("tag_ids", None)
        if tag_ids:
            tag_ids = tag_ids.split(",")
            queryset = queryset.filter(tags__id__in=tag_ids).distinct()

        # 按标题搜索
        search = self.request.query_params.get("search", None)
        if search:
            queryset = queryset.filter(title__icontains=search)

        # 按状态筛选
        status = self.request.query_params.get("status", None)
        if status:
            queryset = queryset.filter(status=status)

        # 按优先级筛选
        priority = self.request.query_params.get("priority", None)
        if priority:
            queryset = queryset.filter(priority=priority)

        return queryset.order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["post"])
    def bulk_delete(self, request):
        task_ids = request.data.get("task_ids", [])
        Task.objects.filter(id__in=task_ids, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"])
    def bulk_update(self, request):
        task_updates = request.data.get("task_updates", [])
        for update in task_updates:
            task_id = update.pop("id")
            Task.objects.filter(id=task_id, user=request.user).update(**update)
        return Response(status=status.HTTP_200_OK)


class TaskTagViewSet(viewsets.ModelViewSet):
    serializer_class = TaskTagSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TaskTag.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
