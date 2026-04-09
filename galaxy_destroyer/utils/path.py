import os
import re
import unicodedata


def sanitize_path(path: str) -> str:
    normalized = unicodedata.normalize("NFC", path)

    if os.name == "nt":
        normalized = normalized.replace("/", "\\")
    else:
        normalized = normalized.replace("\\", "/")

    normalized = re.sub(r"^[/\\]+", "", normalized)

    normalized = re.sub(r"[/\\]+", "_", normalized)

    sanitized = re.sub(r"[^a-zA-Z0-9._\-]", "_", normalized)

    sanitized = sanitized.strip("_")

    return sanitized[:200]
