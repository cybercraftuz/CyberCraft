import json
from pathlib import Path
from django.contrib.auth import get_user_model
from .logs import ws_log


def accept_eula(server_dir: Path):
    (server_dir / "eula.txt").write_text("eula=true\n", encoding="utf-8")


def write_whitelist(server_dir: Path, server_id: int):
    User = get_user_model()
    data = [{"uuid": str(u.uuid), "name": u.username} for u in User.objects.all()]

    (server_dir / "whitelist.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )

    ws_log(server_id, f"[Whitelist] {len(data)} users")


def write_ops(server_dir: Path, server_id: int):
    User = get_user_model()
    data = [
        {
            "uuid": str(u.uuid),
            "name": u.username,
            "level": 4,
            "bypassesPlayerLimit": True,
        }
        for u in User.objects.filter(is_staff=True)
    ]

    (server_dir / "ops.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    ws_log(server_id, f"[Ops] {len(data)} admins")
