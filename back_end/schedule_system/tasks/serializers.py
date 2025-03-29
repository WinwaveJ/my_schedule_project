from rest_framework import serializers
from .models import Task
from app_settings.serializers import TaskCategorySerializer
from django.db import models

# from activities.serializers import ActivitySerializer


class TaskSerializer(serializers.ModelSerializer):
    # activities = ActivitySerializer(many=True, read_only=True)
    category = TaskCategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    estimated_duration = serializers.IntegerField(write_only=True)
    estimated_duration_display = serializers.SerializerMethodField(read_only=True)
    focused_duration = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "due_date",
            "estimated_duration",
            "estimated_duration_display",
            "focused_duration",
            "priority",
            "status",
            "category",
            "category_id",
            "created_at",
            "updated_at",
            "progress",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_estimated_duration_display(self, obj):
        if obj.estimated_duration:
            # 将秒数转换为分钟数，并四舍五入
            return round(obj.estimated_duration.total_seconds() / 60)
        return 0

    def get_focused_duration(self, obj):
        return obj.focused_duration

    def validate_due_date(self, value):
        from django.utils import timezone
        # 如果是更新操作，不验证时间
        if self.instance:
            return value
            
        # 确保比较时使用相同的时区
        if value < timezone.now().astimezone(value.tzinfo):
            raise serializers.ValidationError("截止时间不能是过去的时间")
        return value

    def create(self, validated_data):
        # 从上下文中获取用户
        user = self.context["request"].user
        # 确保validated_data中不包含user字段
        validated_data.pop("user", None)

        # 处理 estimated_duration
        if "estimated_duration" in validated_data:
            from datetime import timedelta
            # 将分钟转换为秒
            minutes = validated_data["estimated_duration"]
            validated_data["estimated_duration"] = timedelta(minutes=minutes)

        # 创建任务
        task = Task.objects.create(user=user, **validated_data)
        return task

    def update(self, instance, validated_data):
        print(f"开始更新任务 {instance.id}")
        print(f"接收到的数据:", validated_data)
        print(f"当前预计时长: {instance.estimated_duration}")
        
        if not validated_data:
            print("警告: 没有提供更新数据")
            return instance
            
        # 处理 estimated_duration
        if "estimated_duration" in validated_data:
            from datetime import timedelta
            try:
                minutes = int(validated_data["estimated_duration"])
                print(f"将 {minutes} 分钟转换为 timedelta")
                validated_data["estimated_duration"] = timedelta(minutes=minutes)
                print(f"转换后的 timedelta: {validated_data['estimated_duration']}")
            except (ValueError, TypeError) as e:
                print(f"转换预计时长时出错: {e}")
                raise serializers.ValidationError(f"无效的预计时长值: {validated_data['estimated_duration']}")
        else:
            # 如果没有提供 estimated_duration，保持原值
            validated_data["estimated_duration"] = instance.estimated_duration

        # 更新任务
        for attr, value in validated_data.items():
            print(f"更新字段 {attr}: {value}")
            setattr(instance, attr, value)
        instance.save()
        print(f"更新后的预计时长: {instance.estimated_duration}")
        return instance
