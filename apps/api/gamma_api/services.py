from __future__ import annotations

from hashlib import sha256
from datetime import datetime
from typing import Protocol

from gamma_core.ids import new_id
from gamma_domain.models import (
    GovernanceClassification,
    IngestionJob,
    Source,
    SourceType,
    Artifact,
)
from gamma_storage import ObjectStore, content_addressed_key


class Repository(Protocol):
    def save_source(self, source: Source, idempotency_key: str | None = None) -> Source: ...

    def get_source(self, source_id: str) -> Source: ...

    def save_ingestion_job(self, job: IngestionJob) -> IngestionJob: ...

    def get_ingestion_job(self, job_id: str) -> IngestionJob: ...

    def save_artifact(self, artifact: Artifact, idempotency_key: str | None = None) -> Artifact: ...

    def get_artifact(self, artifact_id: str) -> Artifact: ...


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
        checksum: str | None = None,
        language: str | None = None,
        owner: str | None = None,
        license: str | None = None,
        jurisdiction: str | None = None,
        acquisition_time: str | None = None,
        ingestion_policy: dict[str, object] | None = None,
        idempotency_key: str | None = None,
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
            license=license,
            jurisdiction=jurisdiction,
            acquisition_time=_parse_datetime(acquisition_time),
            ingestion_policy=ingestion_policy or {},
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


class ArtifactService:
    def __init__(self, repository: Repository, object_store: ObjectStore) -> None:
        self.repository = repository
        self.object_store = object_store

    def register_artifact(
        self,
        *,
        source_id: str,
        data: bytes,
        mime_type: str,
        idempotency_key: str | None,
    ) -> Artifact:
        self.repository.get_source(source_id)
        checksum = sha256(data).hexdigest()
        artifact = Artifact(
            artifact_id=new_id("artifact"),
            source_id=source_id,
            storage_uri=self.object_store.put_immutable(
                content_addressed_key(checksum), data, mime_type
            ),
            checksum=checksum,
            mime_type=mime_type,
            size_bytes=len(data),
        )
        return self.repository.save_artifact(artifact, idempotency_key=idempotency_key)


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
