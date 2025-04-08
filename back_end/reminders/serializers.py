from rest_framework import serializers
from .models import Reminder
from django.utils import timezone


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'current_repeats')

    def validate_reminder_time(self, value):
        """
        验证提醒时间
        """
        if value < timezone.now():
            raise serializers.ValidationError('提醒时间不能早于当前时间')
        return value

    def validate(self, data):
        """
        验证提醒数据
        """
        # 如果是部分更新，只验证提供的字段
        if self.partial:
            return data

        # 验证提醒类型和关联对象
        reminder_type = data.get('reminder_type')
        related_task = data.get('related_task')
        related_activity = data.get('related_activity')

        if reminder_type == 'TASK_DUE' and not related_task:
            raise serializers.ValidationError('任务截止提醒必须关联任务')
        if reminder_type == 'ACTIVITY_START' and not related_activity:
            raise serializers.ValidationError('活动开始提醒必须关联活动')

        # 验证提醒方式
        reminder_method = data.get('reminder_method')
        if reminder_method == 'EMAIL' and not self.context['request'].user.email:
            raise serializers.ValidationError('邮件提醒需要用户设置邮箱')

        return data

    def create(self, validated_data):
        """
        创建提醒时设置用户
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data) 