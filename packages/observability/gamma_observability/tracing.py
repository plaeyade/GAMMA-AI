from __future__ import annotations

import logging


def configure_tracing(service_name: str, enabled: bool) -> None:
    if not enabled:
        logging.getLogger(__name__).info("otel_disabled")
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
    except Exception:
        logging.getLogger(__name__).warning("otel_unavailable")
        return
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    trace.set_tracer_provider(provider)
    logging.getLogger(__name__).info("otel_configured")
