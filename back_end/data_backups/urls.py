from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DataBackupViewSet, BackupScheduleViewSet

router = DefaultRouter()
router.register(r'backups', DataBackupViewSet, basename='backup')
router.register(r'schedules', BackupScheduleViewSet, basename='backup-schedule')

urlpatterns = router.urls