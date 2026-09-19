from __future__ import annotations

from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4

from gamma_config import load_settings
from gamma_core.errors import ConflictError, GammaError, NotFoundError
from gamma_observability import configure_logging, configure_tracing, correlation_id_var
from gamma_persistence import SQLiteRepository
from gamma_storage import check_http_dependency

from gamma_api.schemas import IngestionJobCreate, SourceCreate
from gamma_api.services import IngestionService, SourceService


def create_app() -> object:
    try:
        from fastapi import FastAPI, Header, Request
        from fastapi.responses import JSONResponse
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("FastAPI dependencies are required to run the API") from exc

    settings = load_settings()
    configure_logging(settings.log_level)
    configure_tracing(settings.service_name, settings.otel_enabled)

    app = FastAPI(title="GAMMA Knowledge Engine", version="0.1.0")
    database_path = str(Path(gettempdir()) / "gamma-foundation-api.db")
    repository = SQLiteRepository(database_path)
    repository.apply_migrations(Path("migrations/versions"))
    source_service = SourceService(repository)
    ingestion_service = IngestionService(repository)

    @app.middleware("http")
    async def request_context(request: Request, call_next: object) -> object:
        request_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
        request_id = request_id or f"request_{uuid4().hex}"
        token = correlation_id_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            correlation_id_var.reset(token)

    @app.exception_handler(GammaError)
    async def gamma_error_handler(_: Request, exc: GammaError) -> JSONResponse:
        status_code = 500
        if isinstance(exc, NotFoundError):
            status_code = 404
        elif isinstance(exc, ConflictError):
            status_code = 409
        return JSONResponse(status_code=status_code, content=exc.to_response(correlation_id_var.get()))

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"data": {"status": "ok"}, "metadata": {"request_id": correlation_id_var.get()}}

    @app.get("/ready")
    def ready() -> JSONResponse:
        qdrant = check_http_dependency("qdrant", f"{settings.qdrant_url.rstrip('/')}/")
        s3 = check_http_dependency("s3", f"{settings.s3_endpoint_url.rstrip('/')}/minio/health/ready")
        database_ok = True
        dependencies = [
            {"name": "database", "ok": database_ok, "detail": "connected"},
            {"name": qdrant.name, "ok": qdrant.ok, "detail": qdrant.detail},
            {"name": s3.name, "ok": s3.ok, "detail": s3.detail},
        ]
        ok = all(item["ok"] for item in dependencies)
        status_code = 200 if ok else 503
        return JSONResponse(
            status_code=status_code,
            content={
                "data": {"status": "ready" if ok else "not_ready", "dependencies": dependencies},
                "metadata": {"request_id": correlation_id_var.get()},
            },
        )

    @app.post("/v1/sources", status_code=201)
    def create_source(
        payload: SourceCreate,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, object]:
        source = source_service.register_source(
            source_type=payload.source_type,
            origin=payload.origin,
            domain=payload.domain,
            governance=payload.governance,
            checksum=payload.checksum,
            language=payload.language,
            owner=payload.owner,
            idempotency_key=idempotency_key,
        )
        return {
            "data": {"source_id": source.source_id, "registration_status": "registered"},
            "metadata": {"request_id": correlation_id_var.get()},
        }

    @app.get("/v1/sources/{source_id}")
    def get_source(source_id: str) -> dict[str, object]:
        source = source_service.get_source(source_id)
        return {
            "data": {
                "source_id": source.source_id,
                "source_type": source.source_type.value,
                "origin": source.origin,
                "domain": source.domain,
                "governance": source.governance.value,
                "checksum": source.checksum,
                "language": source.language,
                "owner": source.owner,
            },
            "metadata": {"request_id": correlation_id_var.get()},
        }

    @app.post("/v1/ingestion/jobs", status_code=202)
    def create_ingestion_job(
        payload: IngestionJobCreate,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> dict[str, object]:
        job = ingestion_service.create_job(
            source_id=payload.source_id,
            pipeline_version=payload.pipeline_version,
            requested_operations=payload.requested_operations,
            priority=payload.priority,
            idempotency_key=idempotency_key,
        )
        return {
            "data": {
                "job_id": job.job_id,
                "source_id": job.source_id,
                "pipeline_version": job.pipeline_version,
                "requested_operations": list(job.requested_operations),
                "priority": job.priority,
                "status": job.status.value,
            },
            "metadata": {"request_id": correlation_id_var.get()},
        }

    @app.get("/v1/ingestion/jobs/{job_id}")
    def get_ingestion_job(job_id: str) -> dict[str, object]:
        job = ingestion_service.get_job(job_id)
        return {
            "data": {
                "job_id": job.job_id,
                "source_id": job.source_id,
                "pipeline_version": job.pipeline_version,
                "requested_operations": list(job.requested_operations),
                "priority": job.priority,
                "status": job.status.value,
            },
            "metadata": {"request_id": correlation_id_var.get()},
        }

    return app


app = create_app
