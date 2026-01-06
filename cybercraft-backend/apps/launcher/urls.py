from django.urls import path
from .views import launcher_manifest, LauncherServers, ServerManifest

urlpatterns = [
    path("launcher/manifest.json", launcher_manifest),
    path("launcher/servers/", LauncherServers.as_view(), name="launcher-servers"),
    path("servers/<int:pk>/manifest/", ServerManifest.as_view(), name="server-manifest"),
]
