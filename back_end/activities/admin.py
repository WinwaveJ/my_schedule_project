from django.contrib import admin
from .models import PomodoroActivity, StopwatchActivity


@admin.register(PomodoroActivity)
class PomodoroActivityAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "task",
        "status",
        "pomodoro_count",
        "created_at",
    )
    list_filter = ("status", "user", "created_at")
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(StopwatchActivity)
class StopwatchActivityAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "user",
        "task",
        "status",
        "duration",
        "created_at",
    )
    list_filter = ("status", "user", "created_at")
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "updated_at")
