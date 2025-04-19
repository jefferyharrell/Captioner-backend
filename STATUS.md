# Backend Project Status – Captioner

**Last updated:** 2025-04-19 11:31 PDT

## Project State

- Python virtual environment for the backend is set up and contains all required dependencies (FastAPI, SQLAlchemy, pytest, etc.).
- The backend venv is located at `Captioner-backend/.venv`.
- FastAPI backend for Captioner MVP is under active development.
- Photo SQLAlchemy 2.0 model and DAO layer implemented with full type annotations and TDD coverage.
- Model and DAO are fully tested (pytest), type-checked (Pyright), and linted (Ruff/pre-commit).
- DropboxStorage backend is implemented, supports pagination (fetches all JPEG/PNG recursively, regardless of count), and is fully covered by tests including all error paths (missing token, API errors, pagination errors).
- Backend test coverage is >95% (well above 90% minimum), all lint/type/tests passing and enforced in CI.
- Pre-commit hooks (Ruff, Pyright, YAML, whitespace, coverage, etc.) are enforced locally and in CI.
- Pyright is now installed locally via npm, with configuration in pyproject.toml. The old pyrightconfig.json and third-party pre-commit hook have been removed.
- Ruff is configured to ignore S101 (assert) in tests.
- CI runs on every push and PR to `main`, blocking merges on lint/type/test/coverage failures. Pytest coverage is enforced at 90% minimum.
- SQLite database, image, and thumbnail storage are in place.
- Configuration is via environment variables only; no secrets in code.
- Project rules require Conventional Commits and prohibit newlines in git commit messages.
- Test-driven development (TDD) is strictly followed.
- Photo storage abstraction interface (PhotoStorage) and initial tests added (TDD).

## What Works
- Photo ORM and DAO layer are implemented, tested, and ready for API integration.
- Linting and static type checks enforced (Ruff, local Pyright).
- Pre-commit and CI integration are functional and up-to-date.
- Project structure and configuration match SPEC.md v1.0.4.
- Photo storage abstraction interface (`app/storage.py`) is defined, ABC methods now explicitly raise NotImplementedError, and all error paths are covered by tests.

## In Progress / Next Steps
- Wire up Photo DAO/model to API endpoints per SPEC.md.
- Deploy and configure storage abstraction in FastAPI endpoints.
- Implement S3Storage methods.
- Continue expanding test coverage as new features are added.

## Known Gaps
- Search and ML auto-captioning are out of MVP scope.
- No gallery/grid or upload/delete UI in backend.

---

This summary is designed for LLMs, bots, and humans alike. For full details, see SPEC.md and GitHub.
