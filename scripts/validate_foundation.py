from __future__ import annotations

import ast
import importlib
import json
import os
import re
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATHS = [
    "apps/api",
    "apps/worker",
    "apps/cli",
    "packages/core",
    "packages/config",
    "packages/domain",
    "packages/observability",
    "packages/storage",
    "packages/persistence",
]
for item in MODULE_PATHS:
    sys.path.insert(0, str(ROOT / item))


class CheckFailure(Exception):
    pass


def check(name: str, fn: Callable[[], None], results: list[tuple[str, str, str]]) -> None:
    try:
        fn()
    except Exception as exc:
        results.append((name, "FAIL", f"{exc.__class__.__name__}: {exc}"))
    else:
        results.append((name, "PASS", ""))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def check_required_files() -> None:
    required = [
        "pyproject.toml",
        "docker-compose.yml",
        ".env.example",
        "AGENTS.md",
        "SECURITY.md",
        "README.md",
        "contracts/openapi.json",
        ".github/workflows/ci.yml",
        ".pre-commit-config.yaml",
        "migrations/versions/001_foundation.sql",
        "migrations/versions/002_source_registration_and_artifacts.sql",
    ]
    required += MODULE_PATHS
    missing = [item for item in required if not (ROOT / item).exists()]
    require(not missing, f"missing required foundation paths: {missing}")


def check_python_imports() -> None:
    for module in [
        "gamma_core",
        "gamma_config",
        "gamma_domain",
        "gamma_observability",
        "gamma_storage",
        "gamma_persistence",
        "gamma_api.services",
        "gamma_worker.main",
        "gamma_cli.main",
    ]:
        importlib.import_module(module)


def check_config_validation() -> None:
    from gamma_config import load_settings

    settings = load_settings(
        {
            "GAMMA_ENV": "test",
            "GAMMA_SERVICE_NAME": "gamma-test",
            "GAMMA_DATABASE_URL": "sqlite:///tmp/gamma.db",
            "GAMMA_QDRANT_URL": "http://localhost:6333",
            "GAMMA_S3_ENDPOINT_URL": "http://localhost:9000",
            "GAMMA_S3_BUCKET": "gamma-test",
            "GAMMA_S3_ACCESS_KEY_ID": "local-access",
            "GAMMA_S3_SECRET_ACCESS_KEY": "local-secret",
        }
    )
    require(settings.environment == "test", "settings environment mismatch")
    try:
        load_settings({"GAMMA_ENV": "production", "GAMMA_S3_ACCESS_KEY_ID": "change-me"})
    except ValueError:
        return
    raise CheckFailure("production config accepted insecure defaults")


def check_domain_invariants() -> None:
    from gamma_domain import GovernanceClassification, Source, SourceType

    Source(
        source_id="source_valid",
        source_type=SourceType.DOCUMENT,
        origin={"uri": "synthetic://example"},
        domain="radiation-safety",
        governance=GovernanceClassification.PUBLIC,
        checksum="12345678",
    )
    try:
        Source(
            source_id="bad",
            source_type=SourceType.DOCUMENT,
            origin={},
            domain="",
            governance=GovernanceClassification.PUBLIC,
        )
    except ValueError:
        return
    raise CheckFailure("invalid source passed invariants")


def check_migration_success() -> None:
    migration = ROOT / "migrations/versions/001_foundation.sql"
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        db_path = tmp.name
    try:
        connection = sqlite3.connect(db_path)
        connection.executescript(migration.read_text(encoding="utf-8"))
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        require(
            {"sources", "artifacts", "documents", "document_versions", "ingestion_jobs"}
            <= tables,
            "migration did not create required tables",
        )
    finally:
        connection.close()
        os.unlink(db_path)


def check_persistence_and_idempotency() -> None:
    from gamma_api.services import SourceService
    from gamma_persistence import SQLiteRepository

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        db_path = tmp.name
    try:
        repository = SQLiteRepository(db_path)
        repository.apply_migrations(ROOT / "migrations/versions")
        service = SourceService(repository)
        first = service.register_source(
            source_type="document",
            origin={"uri": "synthetic://source-a"},
            domain="radiation-safety",
            governance="public",
            checksum="abcdef12",
            language="en",
            owner="foundation-test",
            idempotency_key="idem-1",
        )
        second = service.register_source(
            source_type="document",
            origin={"uri": "synthetic://source-a"},
            domain="radiation-safety",
            governance="public",
            checksum="abcdef12",
            language="en",
            owner="foundation-test",
            idempotency_key="idem-1",
        )
        require(first.source_id == second.source_id, "idempotency did not return original source")
    finally:
        try:
            os.unlink(db_path)
        except PermissionError:
            pass


def check_openapi_contract() -> None:
    contract = json.loads((ROOT / "contracts/openapi.json").read_text(encoding="utf-8"))
    require(contract["openapi"].startswith("3."), "OpenAPI 3 contract required")
    paths = set(contract["paths"])
    require(
        {
            "/health",
            "/ready",
            "/v1/sources",
            "/v1/sources/{source_id}",
            "/v1/ingestion/jobs",
            "/v1/ingestion/jobs/{job_id}",
        }
        <= paths,
        "initial API paths missing",
    )
    error_fields = set(contract["components"]["schemas"]["Error"]["required"])
    require(
        {"code", "message", "details", "request_id", "retryable"} <= error_fields,
        "stable error schema missing fields",
    )


def check_negative_scope() -> None:
    forbidden = {"ocr", "embedding", "rag", "knowledge_graph", "clinical_decision"}
    offenders: list[str] = []
    for path in ROOT.rglob("*.py"):
        if "canonical_text" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                lowered = node.name.lower()
                if any(re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", lowered) for term in forbidden):
                    offenders.append(f"{path.relative_to(ROOT)}:{node.name}")
    require(not offenders, f"forbidden Sprint 001 implementation symbols found: {offenders}")


def write_report(results: list[tuple[str, str, str]]) -> None:
    lines = ["# Foundation Sprint 001 Validation Report", ""]
    for name, status, detail in results:
        suffix = f" - {detail}" if detail else ""
        lines.append(f"- {status}: {name}{suffix}")
    (ROOT / "docs/sprint-001/validation-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    results: list[tuple[str, str, str]] = []
    checks: list[tuple[str, Callable[[], None]]] = [
        ("required foundation files", check_required_files),
        ("python imports", check_python_imports),
        ("configuration validation", check_config_validation),
        ("domain invariants", check_domain_invariants),
        ("migration success", check_migration_success),
        ("repository persistence and source idempotency", check_persistence_and_idempotency),
        ("OpenAPI contract validation", check_openapi_contract),
        ("negative scope guard", check_negative_scope),
    ]
    for name, fn in checks:
        check(name, fn, results)
    write_report(results)
    for name, status, detail in results:
        print(f"{status}: {name}" + (f" - {detail}" if detail else ""))
    return 0 if all(status == "PASS" for _, status, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
