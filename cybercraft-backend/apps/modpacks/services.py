import hashlib
import json
from pathlib import Path

ALLOWED_DIRS = ["mods", "resourcepacks", "shaderpacks"]


def sha1(file: Path):
    h = hashlib.sha1()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_manifest(modpack):
    base = Path(modpack.path)
    files = []

    for folder in ALLOWED_DIRS:
        dir_path = base / folder
        if not dir_path.exists():
            continue

        for f in dir_path.rglob("*"):
            if f.is_file():
                files.append(
                    {
                        "path": str(f.relative_to(base)).replace("\\", "/"),
                        "sha1": sha1(f),
                        "size": f.stat().st_size,
                    }
                )

    manifest = {
        "minecraft": modpack.mc_version,
        "loader": modpack.loader,
        "files": files,
    }

    with open(base / "manifest.json", "w", encoding="utf-8") as fp:
        json.dump(manifest, fp, indent=2)

    return manifest
