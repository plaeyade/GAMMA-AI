from __future__ import annotations

from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class DependencyHealth:
    name: str
    ok: bool
    detail: str


def check_http_dependency(name: str, url: str, timeout_seconds: float = 1.0) -> DependencyHealth:
    try:
        request = Request(url, method="GET")
        with urlopen(request, timeout=timeout_seconds) as response:
            return DependencyHealth(name=name, ok=response.status < 500, detail=str(response.status))
    except (OSError, URLError) as exc:
        return DependencyHealth(name=name, ok=False, detail=exc.__class__.__name__)
