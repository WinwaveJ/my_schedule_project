from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskStatsViewSet,
    ActivityStatsViewSet,
    EfficiencyStatsViewSet,
    StatsViewSet
)

router = DefaultRouter()
router.register(r'task-stats', TaskStatsViewSet, basename='task-stats')
router.register(r'activity-stats', ActivityStatsViewSet, basename='activity-stats')
router.register(r'efficiency-stats', EfficiencyStatsViewSet, basename='efficiency-stats')
router.register(r'stats', StatsViewSet, basename='stats')

urlpatterns = [
    path('', include(router.urls)),
] 