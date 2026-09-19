import unittest

from gamma_config import load_settings


class ConfigTests(unittest.TestCase):
    def test_loads_valid_settings(self) -> None:
        settings = load_settings(
            {
                "GAMMA_ENV": "test",
                "GAMMA_SERVICE_NAME": "gamma-test",
                "GAMMA_DATABASE_URL": "sqlite:///tmp/gamma.db",
                "GAMMA_QDRANT_URL": "http://localhost:6333",
                "GAMMA_S3_ENDPOINT_URL": "http://localhost:9000",
                "GAMMA_S3_BUCKET": "gamma-test",
                "GAMMA_S3_ACCESS_KEY_ID": "access",
                "GAMMA_S3_SECRET_ACCESS_KEY": "secret",
            }
        )

        self.assertEqual(settings.environment, "test")

    def test_production_rejects_development_secret(self) -> None:
        with self.assertRaises(ValueError):
            load_settings(
                {
                    "GAMMA_ENV": "production",
                    "GAMMA_SERVICE_NAME": "gamma",
                    "GAMMA_DATABASE_URL": "postgresql://example",
                    "GAMMA_QDRANT_URL": "https://qdrant.example",
                    "GAMMA_S3_ENDPOINT_URL": "https://s3.example",
                    "GAMMA_S3_BUCKET": "gamma",
                    "GAMMA_S3_ACCESS_KEY_ID": "change-me",
                    "GAMMA_S3_SECRET_ACCESS_KEY": "change-me",
                }
            )


if __name__ == "__main__":
    unittest.main()
