import unittest

from gamma_domain import GovernanceClassification, IngestionJob, Source, SourceType


class DomainTests(unittest.TestCase):
    def test_source_requires_stable_prefix_and_origin(self) -> None:
        source = Source(
            source_id="source_123",
            source_type=SourceType.DOCUMENT,
            origin={"uri": "synthetic://doc"},
            domain="radiation-safety",
            governance=GovernanceClassification.PUBLIC,
        )

        self.assertEqual(source.source_id, "source_123")

    def test_rejects_invalid_job_priority(self) -> None:
        with self.assertRaises(ValueError):
            IngestionJob(
                job_id="job_123",
                source_id="source_123",
                pipeline_version="foundation-001",
                requested_operations=("register",),
                priority=11,
            )


if __name__ == "__main__":
    unittest.main()
