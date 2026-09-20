from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    service_name: str
    database_url: str
    qdrant_url: str
    s3_endpoint_url: str
    s3_bucket: str
    s3_access_key_id: str
    s3_secret_access_key: str
    local_artifact_root: str = "data/artifacts"
    log_level: str = "INFO"
    otel_enabled: bool = False

    def validate(self) -> None:
        if self.environment not in {"development", "test", "staging", "production"}:
            raise ValueError("GAMMA_ENV must be development, test, staging or production")
        required = {
            "GAMMA_SERVICE_NAME": self.service_name,
            "GAMMA_DATABASE_URL": self.database_url,
            "GAMMA_QDRANT_URL": self.qdrant_url,
            "GAMMA_S3_ENDPOINT_URL": self.s3_endpoint_url,
            "GAMMA_S3_BUCKET": self.s3_bucket,
            "GAMMA_S3_ACCESS_KEY_ID": self.s3_access_key_id,
            "GAMMA_S3_SECRET_ACCESS_KEY": self.s3_secret_access_key,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"missing required configuration: {', '.join(missing)}")
        if self.environment == "production":
            insecure = {
                "change-me",
                "replace-with-local-development-password",
                "replace-with-local-development-user",
                "dev",
                "test",
            }
            values = {self.s3_access_key_id, self.s3_secret_access_key}
            if values & insecure:
                raise ValueError("production cannot use development credentials")


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    source = env if env is not None else os.environ
    settings = Settings(
        environment=source.get("GAMMA_ENV", "development"),
        service_name=source.get("GAMMA_SERVICE_NAME", "gamma-api"),
        database_url=source.get("GAMMA_DATABASE_URL", "sqlite:///data/gamma-dev.db"),
        qdrant_url=source.get("GAMMA_QDRANT_URL", "http://localhost:6333"),
        s3_endpoint_url=source.get("GAMMA_S3_ENDPOINT_URL", "http://localhost:9000"),
        s3_bucket=source.get("GAMMA_S3_BUCKET", "gamma-dev"),
        s3_access_key_id=source.get("GAMMA_S3_ACCESS_KEY_ID", ""),
        s3_secret_access_key=source.get("GAMMA_S3_SECRET_ACCESS_KEY", ""),
        local_artifact_root=source.get("GAMMA_LOCAL_ARTIFACT_ROOT", "data/artifacts"),
        log_level=source.get("GAMMA_LOG_LEVEL", "INFO"),
        otel_enabled=source.get("GAMMA_OTEL_ENABLED", "false").lower() == "true",
    )
    settings.validate()
    return settings
