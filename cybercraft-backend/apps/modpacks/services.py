import hashlib
import json
from pathlib import Path

ALLOWED_DIRS = ["mods", "resourcepacks", "shaderpacks"]


def sha1(path: Path):
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_manifest(modpack):
    base = Path(modpack.path)
    files = []

    for folder in ALLOWED_DIRS:
        d = base / folder
        if not d.exists():
            continue

        for f in d.rglob("*"):
            if f.is_file():
                files.append(
                    {
                        "path": str(f.relative_to(base)).replace("\\", "/"),
                        "sha1": sha1(f),
                        "size": f.stat().st_size,
                    }
                )

    manifest = {
        "name": modpack.name,
        "minecraft": modpack.mc_version,
        "loader": modpack.loader,
        "files": files,
    }

    (base / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    return manifest
