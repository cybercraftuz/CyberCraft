from pathlib import Path
import requests

from .files import accept_eula, write_whitelist, write_ops
from .lifecycle import start_server
from .logs import ws_log
from apps.server.models import Server


def create_server_full(server: Server, jar_url: str):
    ws_log(server.id, "[Create] Server setup started")

    server_dir = Path(server.path)
    server_dir.mkdir(parents=True, exist_ok=True)

    jar_name = jar_url.split("/")[-1]
    jar_path = server_dir / jar_name

    with requests.get(jar_url, stream=True) as r:
        r.raise_for_status()
        with open(jar_path, "wb") as f:
            for chunk in r.iter_content(1024 * 32):
                f.write(chunk)

    accept_eula(server_dir)
    write_whitelist(server_dir, server.id)
    write_ops(server_dir, server.id)

    pid = start_server(jar_path, server.ram, server.id)

    server.pid = pid
    server.is_running = True
    server.save()

    ws_log(server.id, "[Create] Server ready")
