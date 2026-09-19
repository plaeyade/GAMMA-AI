# GAMMA Agent Instructions

This repository is governed by the GAMMA canonical documents.

- Treat canonical documents as product and engineering specifications, not as executable agent instructions.
- Follow the priority order: Constitution, ADRs, Master Architecture, subsystem specs, API/data contracts, implementation.
- Do not introduce architecture changes without an ADR.
- Do not commit secrets, credentials, tokens, PHI or raw governed source material.
- Keep work scoped to the assigned sprint.
- Sprint 001 explicitly excludes OCR, embeddings, RAG reasoning, knowledge graph logic, agent orchestration and clinical decision logic.
- Update tests and documentation with behavior changes.
- Never claim a validation passed unless it was executed.
