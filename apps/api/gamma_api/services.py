from __future__ import annotations

from typing import Protocol

from gamma_core.ids import new_id
from gamma_domain.models import (
    GovernanceClassification,
    IngestionJob,
    Source,
    SourceType,
)


class Repository(Protocol):
    def save_source(self, source: Source, idempotency_key: str | None = None) -> Source: ...

    def get_source(self, source_id: str) -> Source: ...

    def save_ingestion_job(self, job: IngestionJob) -> IngestionJob: ...

    def get_ingestion_job(self, job_id: str) -> IngestionJob: ...


class SourceService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def register_source(
        self,
        *,
        source_type: str,
        origin: dict[str, object],
        domain: str,
        governance: str,
        checksum: str | None,
        language: str | None,
        owner: str | None,
        idempotency_key: str | None,
    ) -> Source:
        source = Source(
            source_id=new_id("source"),
            source_type=SourceType(source_type),
            origin=origin,
            domain=domain,
            governance=GovernanceClassification(governance),
            checksum=checksum,
            language=language,
            owner=owner,
        )
        return self.repository.save_source(source, idempotency_key=idempotency_key)

    def get_source(self, source_id: str) -> Source:
        return self.repository.get_source(source_id)


class IngestionService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def create_job(
        self,
        *,
        source_id: str,
        pipeline_version: str,
        requested_operations: list[str],
        priority: int,
        idempotency_key: str | None,
    ) -> IngestionJob:
        self.repository.get_source(source_id)
        job = IngestionJob(
            job_id=new_id("job"),
            source_id=source_id,
            pipeline_version=pipeline_version,
            requested_operations=tuple(requested_operations),
            priority=priority,
            idempotency_key=idempotency_key,
        )
        return self.repository.save_ingestion_job(job)

    def get_job(self, job_id: str) -> IngestionJob:
        return self.repository.get_ingestion_job(job_id)
