from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"images", views.ServerImageViewSet, basename="server-image")
router.register(r"", views.ServerViewSet, basename="server")


urlpatterns = [
    path("", include(router.urls)),
    path("create/", views.ServerCreateAPIView.as_view(), name="server-create"),
    path("<int:pk>/control/<str:action>/", views.ServerControlAPIView.as_view(), name="server-control"),
    path("<int:pk>/logs/", views.ServerLogsAPIView.as_view(), name="server-logs"),
]
