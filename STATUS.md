# Backend Project Status – Captioner

**Last updated:** 2025-04-19 08:11 PDT

## Project State

- Python virtual environment for the backend is set up and contains all required dependencies (FastAPI, SQLAlchemy, pytest, etc.).
- The backend venv is located at `Captioner-backend/.venv`.
- FastAPI backend for Captioner MVP is under active development.
- Photo SQLAlchemy 2.0 model and DAO layer implemented with full type annotations and TDD coverage.
- Model and DAO are fully tested (pytest), type-checked (Pyright), and linted (Ruff/pre-commit).
- Pre-commit hooks (Ruff, Pyright, YAML, whitespace, etc.) are enforced locally and in CI.
- Pyright is now installed locally via npm, with configuration in pyproject.toml. The old pyrightconfig.json and third-party pre-commit hook have been removed.
- Ruff is configured to ignore S101 (assert) in tests.
- CI runs on every push and PR to `main`, blocking merges on lint/type/test/coverage failures. Pytest coverage is enforced at 90% minimum.
- SQLite database, image, and thumbnail storage are in place.
- Configuration is via environment variables only; no secrets in code.
- Test-driven development (TDD) is strictly followed.

## What Works
- Photo ORM and DAO layer are implemented, tested, and ready for API integration.
- Linting and static type checks enforced (Ruff, local Pyright).
- Pre-commit and CI integration are functional and up-to-date.
- Project structure and configuration match SPEC.md v1.0.2.

## In Progress / Next Steps
- Wire up Photo DAO/model to API endpoints per SPEC.md.
- Expand test coverage as new features are added.
- No search, ML, or user account features in MVP (see SPEC.md for scope).

## Known Gaps
- Search and ML auto-captioning are out of MVP scope.
- No gallery/grid or upload/delete UI in backend.

---

This summary is designed for LLMs, bots, and humans alike. For full details, see SPEC.md and GitHub.
