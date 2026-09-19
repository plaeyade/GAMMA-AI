# Security Baseline

Sprint 001 establishes a development baseline only.

- Secrets are loaded from environment variables and must not be committed.
- Development data must be synthetic, deidentified, public or governed for the environment.
- API errors use stable machine-readable codes and include request identifiers without exposing stack traces.
- Structured logs must not include credentials, PHI, tokens or raw document contents.
- Dependency scanning is configured in CI with `pip-audit`.
- Destructive persistence changes require an ADR with migration and rollback analysis.
