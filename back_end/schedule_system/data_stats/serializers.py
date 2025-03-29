from rest_framework import serializers
from .models import TaskStats, ActivityStats, EfficiencyStats


class TaskStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskStats
        fields = '__all__'
        read_only_fields = ('user',)


class ActivityStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityStats
        fields = '__all__'
        read_only_fields = ('user',)


class EfficiencyStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EfficiencyStats
        fields = '__all__'
        read_only_fields = ('user',)


class StatsSummarySerializer(serializers.Serializer):
    """
    统计汇总序列化器
    """
    task_stats = TaskStatsSerializer(many=True)
    activity_stats = ActivityStatsSerializer(many=True)
    efficiency_stats = EfficiencyStatsSerializer(many=True) 