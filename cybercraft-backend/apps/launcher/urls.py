from django.urls import path
from .views import launcher_manifest

urlpatterns = [
    path("launcher/manifest.json", launcher_manifest),
]
