from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import IntegrityError
from rest_framework import serializers
from .models import AppSettings, TaskCategory
from .serializers import AppSettingsSerializer, TaskCategorySerializer

# Create your views here.


class AppSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = AppSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AppSettings.objects.filter(user=self.request.user)

    def get_object(self):
        # 获取用户的设置
        try:
            settings = AppSettings.objects.get(id=self.kwargs['pk'])
            if settings.user != self.request.user:
                self.permission_denied(
                    self.request,
                    message='您没有权限访问其他用户的设置'
                )
            return settings
        except AppSettings.DoesNotExist:
            return None

    def create(self, request, *args, **kwargs):
        # 检查用户是否已有设置
        if AppSettings.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "用户设置已存在，请使用更新接口"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # 确保用户只能更新自己的设置
        instance = self.get_object()
        if not instance:
            return Response(
                {"detail": "您没有权限更新其他用户的设置"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        # 确保用户只能查看自己的设置
        instance = self.get_object()
        if not instance:
            return Response(
                {"detail": "您没有权限查看其他用户的设置"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        # 确保用户只能查看自己的设置
        queryset = self.get_queryset()
        if not queryset.exists():
            # 如果用户没有设置，创建一个默认设置
            AppSettings.objects.create(user=request.user)
            queryset = self.get_queryset()
        return super().list(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # 确保用户只能删除自己的设置
        instance = self.get_object()
        if not instance:
            return Response(
                {"detail": "您没有权限删除其他用户的设置"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = TaskCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TaskCategory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise serializers.ValidationError(
                {"name": "您已经创建过相同名称的分类，请使用其他名称"}
            )

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                {"detail": "您已经创建过相同名称的分类，请使用其他名称"},
                status=status.HTTP_400_BAD_REQUEST,
            )
