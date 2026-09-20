import json
import unittest
from pathlib import Path


class OpenAPIContractTests(unittest.TestCase):
    def test_initial_paths_and_error_schema_exist(self) -> None:
        contract = json.loads(Path("contracts/openapi.json").read_text(encoding="utf-8"))

        self.assertIn("/health", contract["paths"])
        self.assertIn("/ready", contract["paths"])
        self.assertIn("/v1/sources", contract["paths"])
        self.assertIn("/v1/ingestion/jobs", contract["paths"])
        self.assertIn("/v1/sources/{source_id}/artifacts", contract["paths"])
        self.assertIn("Artifact", contract["components"]["schemas"])
        self.assertEqual(
            set(contract["components"]["schemas"]["Error"]["required"]),
            {"code", "message", "details", "request_id", "retryable"},
        )


if __name__ == "__main__":
    unittest.main()
