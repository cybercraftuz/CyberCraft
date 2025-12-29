import json
import logging
import threading
import time
import re
from pathlib import Path
from typing import Optional

import requests
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Server
from .utils import ws_log
from .serializers import ServerImageSerializer, ServerSerializer
from .services import (
    get_java_major_version,
    run_installer_and_wait,
    restart_with_fixed_port,
    accept_eula,
    smart_update_properties,
    write_whitelist,
    write_ops,
    terminate_process,
    create_server_full,
)

logger = logging.getLogger(__name__)

MINECRAFT_DIR = Path(settings.MINECRAFT_DIR)
MANIFEST_URL = "https://jars.arcadiatech.org/manifest.json"

PORT_RESERVE_TIMEOUT = 300
MAX_CACHE_KEY_LEN = 250


def _safe_key_component(s: str) -> str:
    if not s:
        return ""
    token = re.sub(r"[^A-Za-z0-9_\-]", "_", s)
    return token[:120]


def _port_cache_key(port: int) -> str:
    return f"reserved_port:{port}"


def reserve_port(start: int = 25565, end: int = 26000) -> int:
    used = set(Server.objects.values_list("port", flat=True))
    for p in range(start, end):
        if p in used:
            continue
        if cache.add(_port_cache_key(p), "1", timeout=PORT_RESERVE_TIMEOUT):
            return p
    raise Exception("Bo'sh port topilmadi")


def fetch_manifest() -> dict:
    r = requests.get(MANIFEST_URL, timeout=10)
    r.raise_for_status()
    return r.json()


def arcadia_list_versions(type_name: str):
    manifest = fetch_manifest()
    types = manifest.get("mc_java_servers", {}).get("types", {})
    if type_name not in types:
        raise Exception("Type topilmadi")
    versions = list(types[type_name].get("versions", {}).keys())
    versions.sort(reverse=True)
    return versions


def arcadia_find(type_name: str, version: str) -> str:
    manifest = fetch_manifest()
    types = manifest.get("mc_java_servers", {}).get("types", {})
    t = types.get(type_name)
    if not t:
        raise Exception("Type not found")
    v = t.get("versions", {}).get(version)
    if not v:
        raise Exception("Version not found")
    url = v.get("url")
    if isinstance(url, list):
        return url[0]
    return url


def api_arcadia_versions(request):
    type_name = request.GET.get("type", "vanilla")
    try:
        return JsonResponse({"versions": arcadia_list_versions(type_name)})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def api_arcadia_download(request):
    type_name = request.GET.get("type")
    version = request.GET.get("version")
    if not type_name or not version:
        return JsonResponse({"error": "type and version required"}, status=400)

    try:
        url = arcadia_find(type_name, version)
        dest = MINECRAFT_DIR / f"{type_name}-{version}.jar"

        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1024 * 32):
                if chunk:
                    f.write(chunk)

        return JsonResponse({"status": "ok", "saved_as": str(dest)})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def server_list(request):
    servers = Server.objects.all()
    return render(request, "pages/server_list.html", {"servers": servers})


def server_create_page(request):
    return render(request, "pages/server_create.html")


def server_detail(request, pk):
    server = get_object_or_404(Server, pk=pk)
    return render(request, "pages/server_detail.html", {"server": server})


@csrf_exempt
def server_create_async(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body.decode())
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = data.get("name", "").strip()
    version = data.get("version")
    server_type = data.get("server_type")
    ram = int(data.get("ram", 1024))

    if not name or not version or not server_type:
        return JsonResponse(
            {"error": "name, version, server_type required"}, status=400
        )

    if Server.objects.filter(name=name).exists():
        return JsonResponse({"error": "Server already exists"}, status=400)

    try:
        port = reserve_port()
    except Exception:
        return JsonResponse({"error": "No free ports"}, status=500)

    try:
        with transaction.atomic():
            srv = Server.objects.create(
                name=name,
                version=version,
                ram=ram,
                port=port,
                path=str(MINECRAFT_DIR / name),
            )
    except Exception:
        return JsonResponse({"error": "Failed to create server"}, status=500)

    def bg():
        try:
            url = arcadia_find(server_type, version)
            create_server_full(
                server_id=srv.id,
                server_dir=Path(srv.path),
                server_type=server_type,
                version=version,
                jar_url=url,
                port=port,
                ram=ram,
            )
        except Exception as e:
            logger.exception("Create failed")
            ws_log(srv.id, f"[Error] {e}")

    threading.Thread(target=bg, daemon=True).start()

    return JsonResponse({"status": "started", "server_id": srv.id})


@csrf_exempt
def server_start(request, pk):
    srv = get_object_or_404(Server, pk=pk)

    if srv.is_running:
        return JsonResponse({"error": "Server already running"}, status=400)

    jars = list(Path(srv.path).glob("*.jar"))
    if not jars:
        return JsonResponse({"error": "Server jar not found"}, status=500)

    pid = restart_with_fixed_port(jars[0], srv.ram, srv.id)

    srv.pid = pid
    srv.is_running = True
    srv.save()

    return JsonResponse({"status": "started"})


@csrf_exempt
def server_stop(request, pk):
    srv = get_object_or_404(Server, pk=pk)

    if not srv.is_running or not srv.pid:
        return JsonResponse({"error": "Server not running"}, status=400)

    terminate_process(srv.pid)

    srv.pid = None
    srv.is_running = False
    srv.save()

    ws_log(srv.id, "[Server] Stopped")

    return JsonResponse({"status": "stopped"})


def server_logs(request, pk):
    server = get_object_or_404(Server, pk=pk)
    log_file = Path(server.path) / "logs" / "latest.log"
    if not log_file.exists():
        return JsonResponse({"error": "Log file not found"}, status=404)

    lines = log_file.read_text(encoding="utf-8").splitlines()
    return JsonResponse({"logs": lines})


class ServerViewSet(viewsets.ModelViewSet):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer


class ServerImageViewSet(viewsets.ViewSet):
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        server_id = request.data.get("server")
        images = request.FILES.getlist("images")

        if not server_id or not images:
            return Response(
                {"error": "server va images maydonlari kerak."},
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
