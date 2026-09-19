from __future__ import annotations

from uuid import uuid4


def new_id(prefix: str) -> str:
    if not prefix or not prefix.replace("_", "").isalnum():
        raise ValueError("identifier prefix must be alphanumeric")
    return f"{prefix}_{uuid4().hex}"
