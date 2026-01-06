import subprocess
import threading
from django.db import close_old_connections
from .logs import ws_log


def start_server(jar_path, ram, server_id):
    proc = subprocess.Popen(
        [
            "java",
            f"-Xms{ram}M",
            f"-Xmx{ram}M",
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
            ws_log(server_id, raw.decode(errors="ignore").rstrip())

    threading.Thread(target=stream, daemon=True).start()

    return proc.pid
