from django.contrib import admin
from .models import AppSettings


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "pomodoro_duration",
        "short_break_duration",
        "long_break_duration",
        "long_break_interval",
    )
    list_filter = ("user",)
    search_fields = ("user__username",)
    readonly_fields = ("created_at", "updated_at")
