import subprocess
import re
from typing import Optional


def get_java_major_version() -> Optional[int]:
    try:
        out = subprocess.check_output(
            ["java", "-version"], stderr=subprocess.STDOUT
        ).decode(errors="ignore")

        m = re.search(r'version "(.*?)"', out)
        if not m:
            return None

        v = m.group(1)
        return int(v.split(".")[1] if v.startswith("1.") else v.split(".")[0])
    except Exception:
        return None
