# GAMMA Foundation Sprint 001

This repository implements the Foundation Sprint 001 baseline for the GAMMA Knowledge Engine.

## Scope

Implemented:

- Required module boundaries: `apps/api`, `apps/worker`, `apps/cli`, `packages/core`, `packages/config`, `packages/domain`, `packages/observability`, `packages/storage`, `packages/persistence`.
- Typed environment configuration.
- Minimal domain models: Source, Artifact, Document, DocumentVersion and IngestionJob.
- FastAPI application skeleton and OpenAPI contract for the initial endpoints.
- Worker and CLI skeletons.
- PostgreSQL-oriented migration SQL with SQLite-compatible local validation.
- Development dependencies for PostgreSQL, Qdrant and S3-compatible object storage.
- Structured logging, request/correlation IDs and optional OpenTelemetry hooks.
- Unit, integration and contract test layout.
- CI, pre-commit and security scanning configuration.

Explicitly not implemented in Sprint 001:

- OCR.
- Embeddings.
- RAG or retrieval reasoning.
- Knowledge graph or ontology logic.
- Clinical decision logic.
- Agent orchestration.

## Local Bootstrap

Create an environment, install development dependencies and start infrastructure:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
docker compose up -d
```

`docker compose` reads the required development credentials from `.env`; use local placeholders only for local development and rotate them freely.

Run the API:

```bash
uvicorn gamma_api.main:create_app --factory --reload
```

Run local validation without external Python packages:

```bash
python scripts/validate_foundation.py
```

Run the full suite after installing dependencies:

```bash
ruff check .
mypy .
pytest
pip-audit
```

## Configuration

Copy `.env.example` to `.env` for local development and replace every placeholder before starting Compose. Production must not use development credentials.

## Sprint 002 Handoff

Sprint 002 adds source registration metadata, raw artifact registration, SHA-256 content-addressed immutable storage, local storage for tests/development and idempotent artifact persistence. It intentionally does not implement extraction, OCR, normalization, chunking, embeddings, retrieval, knowledge graph logic or clinical logic.

See `docs/sprint-002/validation-report.md` and `docs/adr/ADR-0004-object-storage-strategy.md` for the validation record and storage decision.
