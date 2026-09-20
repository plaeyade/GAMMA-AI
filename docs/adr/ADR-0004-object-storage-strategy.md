# ADR-0004 Object Storage Strategy

Status: accepted

Date: 2026-09-19

## Context

Sprint 002 introduces raw artifact storage. Original bytes must remain immutable, and metadata must resolve to a stable storage reference. The application must be testable without requiring a running object-storage service.

## Decision

Artifacts use a content-addressed key derived from the lowercase SHA-256 digest:

`sha256/<first-two-hex>/<full-sha256>`

The repository remains authoritative for artifact metadata. The storage adapter is responsible only for immutable byte storage and URI generation. Sprint 002 provides a filesystem adapter for local development and tests; the existing S3-compatible boundary remains the production integration point.

## Consequences

- Re-uploading identical bytes is idempotent.
- Writing different bytes to an existing content key is rejected.
- Derived processing must create new artifacts and must not overwrite the raw object.
- Local tests do not require MinIO or network access.

## Security Impact

Credentials remain outside Git. Storage URIs are returned as metadata references; authorization remains an API responsibility.

## Migration and Rollback

Migration `002_source_registration_and_artifacts.sql` adds registration metadata and artifact idempotency mappings. Rolling back requires retaining the raw objects and removing only metadata under an approved retention policy.
