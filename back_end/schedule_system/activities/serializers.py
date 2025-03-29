from rest_framework import serializers
from tasks.models import Task
from .models import PomodoroActivity, StopwatchActivity
from tasks.serializers import TaskSerializer


class BaseActivitySerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    task_id = serializers.IntegerField(write_only=True)

    class Meta:
        fields = [
            "id",
            "title",
            "description",
            "user",
            "task",
            "task_id",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "user"]


class PomodoroActivitySerializer(BaseActivitySerializer):
    remaining_time = serializers.SerializerMethodField()
    elapsed_time = serializers.SerializerMethodField()

    class Meta(BaseActivitySerializer.Meta):
        model = PomodoroActivity
        fields = BaseActivitySerializer.Meta.fields + [
            "pomodoro_count",
            "current_pomodoro_start",
            "current_break_start",
            "is_break",
            "is_long_break",
            "remaining_time",
            "elapsed_time",
        ]

    def get_remaining_time(self, obj):
        return obj.get_remaining_time()

    def get_elapsed_time(self, obj):
        return obj.get_elapsed_time()


class StopwatchActivitySerializer(BaseActivitySerializer):
    elapsed_time = serializers.SerializerMethodField()

    class Meta(BaseActivitySerializer.Meta):
        model = StopwatchActivity
        fields = BaseActivitySerializer.Meta.fields + [
            "start_time",
            "end_time",
            "duration",
            "elapsed_time",
        ]

    def get_elapsed_time(self, obj):
        return obj.get_elapsed_time()

    def validate(self, data):
        if "task_id" in data:
            task = Task.objects.filter(
                id=data["task_id"], user=self.context["request"].user
            ).first()
            if not task:
                raise serializers.ValidationError({
                    'task_id': '任务不存在或不属于当前用户'
                })
        return data

    def create(self, validated_data):
        task_id = validated_data.pop("task_id")
        task = Task.objects.get(id=task_id)
        validated_data["task"] = task
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)
