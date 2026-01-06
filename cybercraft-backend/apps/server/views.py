import json
import logging
import threading
import re
from pathlib import Path

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import transaction, close_old_connections
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from .models import Server
from .serializers import ServerSerializer, ServerImageSerializer
from .utils import ws_log
from .services import (
    create_server_full,
    restart_with_fixed_port,
    terminate_process,
)

logger = logging.getLogger(__name__)

MINECRAFT_DIR = Path(settings.MINECRAFT_DIR)

ARCADIA_MANIFEST_URL = "https://jars.arcadiatech.org/manifest.json"

PORT_RESERVE_TIMEOUT = 300


def _port_cache_key(port: int) -> str:
    return f"reserved_port:{port}"


def reserve_port(start: int = 25565, end: int = 26000) -> int:
    used = set(Server.objects.values_list("port", flat=True))
    for port in range(start, end):
        if port in used:
            continue
        if cache.add(_port_cache_key(port), "1", timeout=PORT_RESERVE_TIMEOUT):
            return port
    raise RuntimeError("No free ports available")


def fetch_arcadia_manifest() -> dict:
    r = requests.get(ARCADIA_MANIFEST_URL, timeout=10)
    r.raise_for_status()
    return r.json()


def arcadia_find(server_type: str, version: str) -> str:
    manifest = fetch_arcadia_manifest()
    types = manifest.get("mc_java_servers", {}).get("types", {})
    t = types.get(server_type)
    if not t:
        raise ValueError("Invalid server type")

    v = t.get("versions", {}).get(version)
    if not v:
        raise ValueError("Invalid version")

    url = v.get("url")
    return url[0] if isinstance(url, list) else url


class ServerCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        data = request.data

        name = data.get("name", "").strip()
        version = data.get("version")
        server_type = data.get("server_type")
        ram = int(data.get("ram", 1024))
        modpack_id = data.get("modpack")

        if not all([name, version, server_type, modpack_id]):
            return Response(
                {"error": "name, version, server_type, modpack required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Server.objects.filter(name=name).exists():
            return Response(
                {"error": "Server with this name already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            port = reserve_port()
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        with transaction.atomic():
            server = Server.objects.create(
                name=name,
                version=version,
                ram=ram,
                port=port,
                path=str(MINECRAFT_DIR / name),
                modpack_id=modpack_id,
            )

        def bg_task(server_id: int):
            close_old_connections()
            try:
                url = arcadia_find(server_type, version)
                create_server_full(
                    server=Server.objects.get(id=server_id),
                    jar_url=url,
                )
            except Exception as e:
                logger.exception("Server creation failed")
                ws_log(server_id, f"[Error] {e}")
            finally:
                close_old_connections()

        threading.Thread(target=bg_task, args=(server.id,), daemon=True).start()

        return Response(
            {"status": "creating", "server_id": server.id},
            status=status.HTTP_201_CREATED,
        )


class ServerControlAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk, action):
        server = get_object_or_404(Server, pk=pk)

        if action == "start":
            if server.is_running:
                return Response({"error": "Already running"}, status=400)

            jars = list(Path(server.path).glob("*.jar"))
            if not jars:
                return Response({"error": "Server jar not found"}, status=500)

            pid = restart_with_fixed_port(jars[0], server.ram, server.id)
            server.pid = pid
            server.is_running = True
            server.save()

            return Response({"status": "started"})

        if action == "stop":
            if not server.is_running or not server.pid:
                return Response({"error": "Not running"}, status=400)

            terminate_process(server.pid)
            server.pid = None
            server.is_running = False
            server.save()

            ws_log(server.id, "[Server] Stopped")
            return Response({"status": "stopped"})

        return Response({"error": "Invalid action"}, status=400)


class ServerLogsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, pk):
        server = get_object_or_404(Server, pk=pk)
        log_file = Path(server.path) / "logs" / "latest.log"

        if not log_file.exists():
            return Response({"logs": []})

        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-500:]

        return Response({"logs": lines})


class ServerViewSet(ModelViewSet):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]


class ServerImageViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request):
        server_id = request.data.get("server")
        images = request.FILES.getlist("images")

        if not server_id or not images:
            return Response(
                {"error": "server and images required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = []
        for image in images:
            serializer = ServerImageSerializer(
                data={"server": server_id, "image": image}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            created.append(serializer.data)

        return Response(created, status=status.HTTP_201_CREATED)
