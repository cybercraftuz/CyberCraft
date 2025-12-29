import os
import subprocess
import time
from pathlib import Path
from typing import Optional
import json

from django.contrib.auth import get_user_model
from django.db import close_old_connections

from .utils import ws_log
from .models import Server


def get_java_major_version() -> Optional[int]:
    try:
        out = subprocess.check_output(
            ["java", "-version"], stderr=subprocess.STDOUT
        ).decode(errors="ignore")

        import re

        m = re.search(r'version "(.*?)"', out)
        if not m:
            return None

        v = m.group(1)
        if v.startswith("1."):
            return int(v.split(".")[1])
        return int(v.split(".")[0])
    except Exception:
        return None


def run_installer_and_wait(
    installer_jar: Path,
    server_dir: Path,
    server_id: int,
    timeout: int = 300,
) -> bool:
    ws_log(server_id, f"[Installer] Starting installer: {installer_jar.name}")

    proc = subprocess.Popen(
        ["java", "-jar", str(installer_jar), "--installServer"],
        cwd=server_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    start = time.time()

    for raw in proc.stdout:
        line = raw.decode("utf-8", errors="ignore").rstrip()
        ws_log(server_id, f"[Installer] {line}")

        if time.time() - start > timeout:
            proc.kill()
            ws_log(server_id, "[Error] Installer timeout exceeded")
            return False

    code = proc.wait()
    if code == 0:
        ws_log(server_id, "[Installer] Completed successfully")
        return True

    ws_log(server_id, f"[Error] Installer failed (code={code})")
    return False


def restart_with_fixed_port(
    jar_path: Path,
    ram_mb: int,
    server_id: int,
) -> int:
    ws_log(server_id, f"[Server] Starting: {jar_path.name}")

    proc = subprocess.Popen(
        [
            "java",
            f"-Xmx{ram_mb}M",
            f"-Xms{ram_mb}M",
            "-jar",
            str(jar_path),
            "nogui",
        ],
        cwd=jar_path.parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )

    def stream():
        close_old_connections()
        for raw in proc.stdout:
            line = raw.decode("utf-8", errors="ignore").rstrip()
            ws_log(server_id, f"[Server] {line}")

    import threading

    threading.Thread(target=stream, daemon=True).start()

    ws_log(server_id, f"[Server] Process started (PID={proc.pid})")
    return proc.pid


def terminate_process(pid: int):
    try:
        if os.name == "nt":
            subprocess.call(
                ["taskkill", "/F", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            os.kill(pid, 9)
    except Exception:
        pass


def accept_eula(server_dir: Path):
    (server_dir / "eula.txt").write_text("eula=true\n", encoding="utf-8")


def write_whitelist(server_dir: Path, server_id: int):
    User = get_user_model()
    entries = [{"uuid": str(u.uuid), "name": u.username} for u in User.objects.all()]

    (server_dir / "whitelist.json").write_text(
        json.dumps(entries, indent=2),
        encoding="utf-8",
    )

    ws_log(server_id, f"[Whitelist] {len(entries)} users synced")


def write_ops(server_dir: Path, server_id: int):
    User = get_user_model()
    entries = [
        {
            "uuid": str(u.uuid),
            "name": u.username,
            "level": 4,
            "bypassesPlayerLimit": True,
        }
        for u in User.objects.filter(is_staff=True)
    ]

    (server_dir / "ops.json").write_text(
        json.dumps(entries, indent=2),
        encoding="utf-8",
    )

    ws_log(server_id, f"[Ops] {len(entries)} users written")


def smart_update_properties(path: Path, updates: dict):
    props = {}

    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                props[k] = v

    props.update(updates)

    with open(path, "w", encoding="utf-8") as f:
        for k, v in props.items():
            f.write(f"{k}={v}\n")


def create_server_full(
    server_id: int,
    server_dir: Path,
    server_type: str,
    version: str,
    jar_url: str,
    port: int,
    ram: int,
):
    ws_log(server_id, "[Info] Server yaratish boshlandi")

    server_dir.mkdir(parents=True, exist_ok=True)

    filename = jar_url.split("/")[-1]
    jar_path = server_dir / filename

    ws_log(server_id, f"[Download] {filename}")
    import requests

    with requests.get(jar_url, stream=True) as r:
        r.raise_for_status()
        with open(jar_path, "wb") as fh:
            for chunk in r.iter_content(1024 * 32):
                if chunk:
                    fh.write(chunk)

    ws_log(server_id, "[Download] Completed")

    is_installer = "installer" in filename.lower()

    if is_installer:
        ok = run_installer_and_wait(jar_path, server_dir, server_id)
        if not ok:
            return

        jars = [
            p for p in server_dir.rglob("*.jar") if "installer" not in p.name.lower()
        ]
        jar_path = jars[0]

    accept_eula(server_dir)

    smart_update_properties(
        server_dir / "server.properties",
        {
            "server-port": port,
            "query.port": port,
            "online-mode": "false",
            "white-list": "true",
            "motd": f"Server {server_id}",
        },
    )

    write_whitelist(server_dir, server_id)
    write_ops(server_dir, server_id)

    pid = restart_with_fixed_port(jar_path, ram, server_id)

    srv = Server.objects.get(id=server_id)
    srv.pid = pid
    srv.is_running = True
    srv.save()

    ws_log(server_id, "[Info] Server fully ready")
