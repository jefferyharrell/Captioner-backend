# Backend Project Status – Captioner

**Last updated:** 2025-04-18

## Project State
- FastAPI backend for Captioner MVP is under active development.
- Core endpoints are defined in SPEC.md but have not yet been implemented (TDD baseline only).
- Pre-commit hooks (Ruff, Pyright, YAML, whitespace, etc.) are enforced locally and in CI.
- Pyright is now installed locally via npm, with configuration in pyproject.toml. The old pyrightconfig.json and third-party pre-commit hook have been removed.
- Ruff is configured to ignore S101 (assert) in tests.
- CI runs on every push and PR to `main`, blocking merges on lint/type/test/coverage failures. Pytest coverage is enforced at 90% minimum.
- SQLite database, image, and thumbnail storage are in place.
- Configuration is via environment variables only; no secrets in code.
- Test-driven development (TDD) is strictly followed.

## What Works
- Linting and static type checks enforced (Ruff, local Pyright).
- Pre-commit and CI integration are functional and up-to-date.
- Project structure and configuration match SPEC.md v1.0.2.

## In Progress / Next Steps
- Implementing and refining API endpoints per SPEC.md (none implemented yet).
- Expanding test coverage and ensuring DB/filesystem isolation in tests.
- No search, ML, or user account features in MVP (see SPEC.md for scope).

## Known Gaps
- Search and ML auto-captioning are out of MVP scope.
- No gallery/grid or upload/delete UI in backend.

---

This summary is designed for LLMs, bots, and humans alike. For full details, see SPEC.md and GitHub.
