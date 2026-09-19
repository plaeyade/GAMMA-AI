from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from gamma_core.errors import ConflictError, NotFoundError
from gamma_domain.models import (
    GovernanceClassification,
    IngestionJob,
    IngestionStatus,
    Source,
    SourceType,
)


class SQLiteRepository:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def apply_migrations(self, migration_dir: Path) -> None:
        with self.connect() as connection:
            for migration in sorted(migration_dir.glob("*.sql")):
                sql = migration.read_text(encoding="utf-8")
                if self.database_path == ":memory:":
                    sql = sql.replace("JSONB", "TEXT")
                connection.executescript(sql)

    def save_source(self, source: Source, idempotency_key: str | None = None) -> Source:
        with self.connect() as connection:
            if idempotency_key:
                existing = connection.execute(
                    "SELECT source_id FROM source_idempotency_keys WHERE idempotency_key = ?",
                    (idempotency_key,),
                ).fetchone()
                if existing:
                    stored = self.get_source(existing["source_id"])
                    if _source_fingerprint(stored) != _source_fingerprint(source):
                        raise ConflictError(
                            "IDEMPOTENCY_CONFLICT",
                            "Idempotency-Key was already used for a different source request.",
                            {"idempotency_key": idempotency_key},
                        )
                    return stored
            connection.execute(
                """
                INSERT INTO sources (
                    source_id, source_type, origin, domain, governance, checksum,
                    language, owner, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source.source_id,
                    source.source_type.value,
                    json.dumps(source.origin, sort_keys=True),
                    source.domain,
                    source.governance.value,
                    source.checksum,
                    source.language,
                    source.owner,
                    source.created_at.isoformat(),
                ),
            )
            if idempotency_key:
                connection.execute(
                    """
                    INSERT INTO source_idempotency_keys (idempotency_key, source_id)
                    VALUES (?, ?)
                    """,
                    (idempotency_key, source.source_id),
                )
            return source

    def get_source(self, source_id: str) -> Source:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM sources WHERE source_id = ?",
                (source_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError("source", source_id)
        return Source(
            source_id=row["source_id"],
            source_type=SourceType(row["source_type"]),
            origin=json.loads(row["origin"]),
            domain=row["domain"],
            governance=GovernanceClassification(row["governance"]),
            checksum=row["checksum"],
            language=row["language"],
            owner=row["owner"],
        )

    def save_ingestion_job(self, job: IngestionJob) -> IngestionJob:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO ingestion_jobs (
                    job_id, source_id, pipeline_version, requested_operations,
                    priority, status, idempotency_key, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.source_id,
                    job.pipeline_version,
                    json.dumps(list(job.requested_operations)),
                    job.priority,
                    job.status.value,
                    job.idempotency_key,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                ),
            )
            return job

    def get_ingestion_job(self, job_id: str) -> IngestionJob:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM ingestion_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError("job", job_id)
        return IngestionJob(
            job_id=row["job_id"],
            source_id=row["source_id"],
            pipeline_version=row["pipeline_version"],
            requested_operations=tuple(json.loads(row["requested_operations"])),
            priority=row["priority"],
            status=IngestionStatus(row["status"]),
            idempotency_key=row["idempotency_key"],
        )


def _source_fingerprint(source: Source) -> tuple[object, ...]:
    return (
        source.source_type.value,
        json.dumps(source.origin, sort_keys=True),
        source.domain,
        source.governance.value,
        source.checksum,
        source.language,
        source.owner,
    )
