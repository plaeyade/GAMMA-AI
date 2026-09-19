import tempfile
import unittest
from pathlib import Path

from gamma_api.services import IngestionService, SourceService
from gamma_persistence import SQLiteRepository


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


if __name__ == "__main__":
    unittest.main()
