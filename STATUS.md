# Backend Project Status – Captioner

**Last updated:** 2025-04-18

## Project State
- FastAPI backend for Captioner MVP is under active development.
- Core endpoints are defined in SPEC.md and being implemented/tested.
- Pre-commit hooks (Ruff, Pyright, YAML, whitespace, etc.) are enforced locally and in CI.
- CI runs on every push and PR to `main`, blocking merges on lint/type/test failures.
- SQLite database, image, and thumbnail storage are in place.
- Configuration is via environment variables only; no secrets in code.
- Test-driven development (TDD) is strictly followed.

## What Works
- Linting and static type checks enforced (Ruff, Pyright).
- Pre-commit and CI integration are functional.
- Project structure and configuration match SPEC.md v1.0.2.

## In Progress / Next Steps
- Implementing and refining API endpoints per SPEC.md.
- Expanding test coverage and ensuring DB/filesystem isolation in tests.
- No search, ML, or user account features in MVP (see SPEC.md for scope).

## Known Gaps
- Search and ML auto-captioning are out of MVP scope.
- No gallery/grid or upload/delete UI in backend.

---

This summary is designed for LLMs, bots, and humans alike. For full details, see SPEC.md and GitHub.
