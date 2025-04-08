from rest_framework import serializers
from .models import AppSettings, TaskCategory


class AppSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppSettings
        fields = [
            "id",
            "pomodoro_duration",
            "short_break_duration",
            "long_break_duration",
            "long_break_interval",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        # 验证番茄钟时长
        if "pomodoro_duration" in data and data["pomodoro_duration"] <= 0:
            raise serializers.ValidationError(
                {"pomodoro_duration": "番茄钟时长必须大于0"}
            )

        # 验证短休息时长
        if "short_break_duration" in data and data["short_break_duration"] <= 0:
            raise serializers.ValidationError(
                {"short_break_duration": "短休息时长必须大于0"}
            )

        # 验证长休息时长
        if "long_break_duration" in data and data["long_break_duration"] <= 0:
            raise serializers.ValidationError(
                {"long_break_duration": "长休息时长必须大于0"}
            )

        # 验证长休息间隔
        if "long_break_interval" in data and data["long_break_interval"] <= 0:
            raise serializers.ValidationError(
                {"long_break_interval": "长休息间隔必须大于0"}
            )

        return data

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class TaskCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskCategory
        fields = ['id', 'name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
