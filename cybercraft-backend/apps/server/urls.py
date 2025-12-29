from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"images", views.ServerImageViewSet, basename="server-image")
router.register(r"", views.ServerViewSet, basename="server")

urlpatterns = [
    path("", views.server_list, name="server-list"),
    path("create/", views.server_create_page, name="server-create"),
    path("create-async/", views.server_create_async, name="server-create-async"),
    path("arcadia/versions/", views.api_arcadia_versions, name="arcadia-versions"),
    path("arcadia/download/", views.api_arcadia_download, name="arcadia-download"),
    path("<int:pk>/", views.server_detail, name="server-detail"),
    path("<int:pk>/start/", views.server_start, name="server-start"),
    path("<int:pk>/stop/", views.server_stop, name="server-stop"),
    path("<int:pk>/logs/", views.server_logs, name="server-logs"),
    path("", include(router.urls)),
]
