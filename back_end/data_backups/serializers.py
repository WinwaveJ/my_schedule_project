from rest_framework import serializers
from .models import DataBackup, BackupSchedule


class DataBackupSerializer(serializers.ModelSerializer):
    file_size_display = serializers.CharField(source='get_file_size_display', read_only=True)

    class Meta:
        model = DataBackup
        fields = [
            'id', 'user', 'backup_type', 'status', 'created_at',
            'completed_at', 'file_path', 'file_size', 'file_size_display',
            'included_modules', 'error_message', 'metadata'
        ]
        read_only_fields = ['user', 'created_at', 'completed_at', 'file_size', 'file_size_display']


class BackupScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupSchedule
        fields = [
            'id', 'user', 'name', 'frequency', 'backup_type',
            'is_active', 'last_run', 'next_run', 'retention_days',
            'included_modules', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'last_run', 'next_run', 'created_at', 'updated_at']

    def validate(self, data):
        """
        验证备份计划数据
        """
        if not data.get('included_modules'):
            raise serializers.ValidationError('必须选择至少一个要备份的模块')
        return data

    def create(self, validated_data):
        """
        创建备份计划时设置用户和下次运行时间
        """
        validated_data['user'] = self.context['request'].user
        validated_data['next_run'] = self.Meta.model(**validated_data).calculate_next_run()
        return super().create(validated_data)


class BackupScheduleDetailSerializer(BackupScheduleSerializer):
    """
    包含相关备份历史的详细序列化器
    """
    recent_backups = serializers.SerializerMethodField()

    class Meta(BackupScheduleSerializer.Meta):
        fields = BackupScheduleSerializer.Meta.fields + ['recent_backups']

    def get_recent_backups(self, obj):
        """
        获取最近的5个备份记录
        """
        recent_backups = obj.user.data_backups.filter(
            backup_type=obj.backup_type,
            included_modules=obj.included_modules
        ).order_by('-created_at')[:5]
        return DataBackupSerializer(recent_backups, many=True).data 