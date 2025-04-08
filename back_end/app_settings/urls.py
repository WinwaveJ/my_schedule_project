from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AppSettingsViewSet, TaskCategoryViewSet

router = DefaultRouter()
router.register(r"settings", AppSettingsViewSet, basename="appsettings")
router.register(r"categories", TaskCategoryViewSet, basename="taskcategory")

urlpatterns = [
    path("", include(router.urls)),
]
