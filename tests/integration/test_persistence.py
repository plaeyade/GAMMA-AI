import tempfile
import unittest
from hashlib import sha256
from pathlib import Path

from gamma_api.services import ArtifactService, IngestionService, SourceService
from gamma_persistence import SQLiteRepository
from gamma_domain import Artifact
from gamma_storage import LocalImmutableObjectStore


class PersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        self.repository = SQLiteRepository(self.tmp.name)
        self.repository.apply_migrations(Path("migrations/versions"))

    def test_source_idempotency_and_job_persistence(self) -> None:
        source_service = SourceService(self.repository)
        ingestion_service = IngestionService(self.repository)

        source = source_service.register_source(
            source_type="document",
            origin={"uri": "synthetic://doc"},
            domain="radiation-safety",
            governance="public",
            checksum="abcdef12",
            language="en",
            owner=None,
            idempotency_key="source-key",
        )
        again = source_service.register_source(
            source_type="document",
            origin={"uri": "synthetic://doc"},
            domain="radiation-safety",
            governance="public",
            checksum="abcdef12",
            language="en",
            owner=None,
            idempotency_key="source-key",
        )
        job = ingestion_service.create_job(
            source_id=source.source_id,
            pipeline_version="foundation-001",
            requested_operations=["register"],
            priority=5,
            idempotency_key="job-key",
        )

        self.assertEqual(source.source_id, again.source_id)
        self.assertEqual(self.repository.get_ingestion_job(job.job_id).status.value, "queued")

    def test_source_metadata_and_artifact_idempotency(self) -> None:
        source_service = SourceService(self.repository)
        source = source_service.register_source(
            source_type="document",
            origin={"uri": "synthetic://metadata"},
            domain="radiation-safety",
            governance="public",
            checksum="abcdef12",
            language="en",
            owner="test",
            license="CC-BY",
            jurisdiction="MX",
            acquisition_time="2026-09-19T12:00:00+00:00",
            ingestion_policy={"operations": ["register"]},
            idempotency_key="source-metadata",
        )
        loaded = self.repository.get_source(source.source_id)
        self.assertEqual(loaded.license, "CC-BY")
        self.assertEqual(loaded.jurisdiction, "MX")
        payload = b"immutable"
        artifact = Artifact(
            artifact_id="artifact_test",
            source_id=source.source_id,
            storage_uri="file:///tmp/immutable",
            checksum=sha256(payload).hexdigest(),
            mime_type="text/plain",
            size_bytes=len(payload),
        )
        first = self.repository.save_artifact(artifact, idempotency_key="artifact-key")
        again = self.repository.save_artifact(artifact, idempotency_key="artifact-key")
        self.assertEqual(first.artifact_id, again.artifact_id)

    def test_artifact_service_persists_content_addressed_artifact(self) -> None:
        source = SourceService(self.repository).register_source(
            source_type="document",
            origin={"uri": "synthetic://artifact-service"},
            domain="radiation-safety",
            governance="public",
            idempotency_key="artifact-service-source",
        )
        with tempfile.TemporaryDirectory() as root:
            artifact = ArtifactService(
                self.repository, LocalImmutableObjectStore(Path(root))
            ).register_artifact(
                source_id=source.source_id,
                data=b"raw bytes",
                mime_type="application/octet-stream",
                idempotency_key="artifact-service-key",
            )
            self.assertIn("sha256/", artifact.storage_uri)
            self.assertEqual(artifact.size_bytes, 9)


if __name__ == "__main__":
    unittest.main()
