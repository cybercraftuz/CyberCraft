from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.server.models import Server
from apps.modpacks.services import generate_manifest
import json
from pathlib import Path
from django.http import JsonResponse, Http404
from .models import LauncherBuild


def launcher_manifest(request):
    build = LauncherBuild.objects.filter(is_active=True).first()
    if not build:
        raise Http404("Launcher build not found")

    return JsonResponse(
        {
            "version": build.version,
            "buildNumber": build.build_number,
            "asar": {
                "url": request.build_absolute_uri(build.asar_file.url),
                "sha256": build.sha256,
            },
        }
    )


class LauncherServers(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        servers = Server.objects.all()
        return Response(
            [
                {
                    "id": s.id,
                    "name": s.name,
                    "mc_version": s.modpack.mc_version,
                    "loader": s.modpack.loader,
                }
                for s in servers
            ]
        )


class ServerManifest(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        server = Server.objects.get(pk=pk)
        base = Path(server.modpack.path)
        manifest_path = base / "manifest.json"

        if not manifest_path.exists():
            generate_manifest(server.modpack)

        return Response(json.loads(manifest_path.read_text()))
