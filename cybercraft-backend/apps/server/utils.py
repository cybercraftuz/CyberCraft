import re
import uuid
import asyncio
from pathlib import Path
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Server


def normalize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)


def ws_log(server_id: int, line: str):
    async_to_sync(get_channel_layer().group_send)(
        f"progress_{server_id}", {"type": "send_log", "log": line}
    )

    server = Server.objects.filter(id=server_id).first()
    if not server:
        return

    log_dir = Path(server.path) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "latest.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def minecraft_offline_uuid(username: str) -> str:
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, "OfflinePlayer:" + username))
