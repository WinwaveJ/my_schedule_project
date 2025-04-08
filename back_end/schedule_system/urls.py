"""
URL configuration for schedule_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/", include("users.urls")),  # 添加用户模块的路由
    path("api/", include("tasks.urls")),  # 添加任务模块的路由
    path("api/", include("activities.urls")),  # 添加活动模块的路由
    path("api/", include("app_settings.urls")),  # 添加应用设置模块的路由
    path("api/", include("reminders.urls")),  # 添加提醒模块的路由
    path("api/", include("data_stats.urls")),  # 添加数据统计模块的路由
    path("api/", include("data_backups.urls")),  # 添加数据备份模块的路由
]
