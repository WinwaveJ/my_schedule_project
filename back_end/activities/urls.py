from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PomodoroActivityViewSet, StopwatchActivityViewSet

router = DefaultRouter()
router.register(r"pomodoro-activities", PomodoroActivityViewSet, basename="pomodoro-activity")
router.register(r"stopwatch-activities", StopwatchActivityViewSet, basename="stopwatch-activity")

urlpatterns = [
    path("", include(router.urls)),
]
