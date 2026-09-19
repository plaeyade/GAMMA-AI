from __future__ import annotations

import logging

from gamma_config import load_settings
from gamma_observability import configure_logging, configure_tracing


def main() -> int:
    settings = load_settings()
    configure_logging(settings.log_level)
    configure_tracing("gamma-worker", settings.otel_enabled)
    logging.getLogger(__name__).info("worker_started_noop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
