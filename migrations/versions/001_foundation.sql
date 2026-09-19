CREATE TABLE IF NOT EXISTS sources (
  source_id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  origin JSONB NOT NULL,
  domain TEXT NOT NULL,
  governance TEXT NOT NULL,
  checksum TEXT,
  language TEXT,
  owner TEXT,
  created_at TEXT NOT NULL,
  CHECK (source_id LIKE 'source_%')
);

CREATE TABLE IF NOT EXISTS source_idempotency_keys (
  idempotency_key TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id)
);

CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  storage_uri TEXT NOT NULL UNIQUE,
  checksum TEXT NOT NULL,
  mime_type TEXT NOT NULL,
  size_bytes INTEGER NOT NULL CHECK (size_bytes >= 0),
  created_at TEXT NOT NULL,
  CHECK (artifact_id LIKE 'artifact_%')
);

CREATE TABLE IF NOT EXISTS documents (
  document_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  current_version_id TEXT,
  created_at TEXT NOT NULL,
  CHECK (document_id LIKE 'document_%')
);

CREATE TABLE IF NOT EXISTS document_versions (
  document_version_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(document_id),
  artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
  version_number INTEGER NOT NULL CHECK (version_number >= 1),
  pipeline_version TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (document_id, version_number),
  CHECK (document_version_id LIKE 'document_version_%')
);

CREATE TABLE IF NOT EXISTS ingestion_jobs (
  job_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  pipeline_version TEXT NOT NULL,
  requested_operations JSONB NOT NULL,
  priority INTEGER NOT NULL CHECK (priority BETWEEN 0 AND 10),
  status TEXT NOT NULL,
  idempotency_key TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  CHECK (job_id LIKE 'job_%')
);
