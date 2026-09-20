CREATE TABLE IF NOT EXISTS source_registration_metadata (
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (source_id, key)
);

CREATE TABLE IF NOT EXISTS artifact_idempotency_keys (
  idempotency_key TEXT PRIMARY KEY,
  artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_artifacts_source_checksum
  ON artifacts(source_id, checksum);
