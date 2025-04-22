# Plan: Replace Authlib with PyJWT

**Goal:** Replace the `Authlib` library with `PyJWT` for handling JSON Web Tokens (JWTs) in the backend application (`app/utils/jwt.py`).

**Rationale:**

*   **Simplify Dependencies:** Reduce the number of dependencies and potential points of failure.
*   **Improve Typing:** Address persistent Pyright type checking warnings and complexity associated with `Authlib` and its custom stubs (see Memory `85764850-c08f-43d9-89a5-4e08a9906aaa`, `40eecaee-8751-4fc0-aace-86f4ed3a5430`). `PyJWT` generally has better-maintained type hints (`types-pyjwt`).

**Steps:**

1.  **Install Dependencies:**
    *   Add `pyjwt[crypto]` to `requirements.txt`.
    *   Add `types-pyjwt` to `requirements-dev.txt`.
    *   Run `pip install -r requirements.txt -r requirements-dev.txt` within the virtual environment (`.venv`).

2.  **Identify Authlib Usage:**
    *   Locate all code currently using `Authlib`. This is primarily expected within `app/utils/jwt.py`.
    *   Use `grep_search` if needed to confirm all locations.

3.  **Implement PyJWT Logic:**
    *   Rewrite the JWT generation (`create_access_token`) and verification (`verify_access_token`) functions in `app/utils/jwt.py` using `PyJWT`.
    *   Ensure the new implementation maintains the same functionality and security standards (e.g., algorithm, claims, error handling).

4.  **Update Type Hints:**
    *   Adjust function signatures and internal type hints in `app/utils/jwt.py` and any calling code to align with `PyJWT` types.

5.  **Remove Authlib:**
    *   Remove `Authlib` from `requirements.txt`.
    *   Remove the custom `Authlib` stubs directory (`typings/authlib/`).
    *   Update `pyproject.toml` to remove any `Authlib`-specific configurations or ignores (check Ruff excludes, Pyright settings). Check `.pre-commit-config.yaml` as well.
    *   Run `pip uninstall authlib` and `pip install -r requirements.txt` to clean up.

6.  **Verification & Testing (The Gauntlet):**
    *   Run `ruff check . --fix` and address any remaining issues.
    *   Run `npx pyright .` and fix all reported type errors (except known unavoidable ones in `tests/conftest.py`).
    *   Run `pytest --cov=app --cov-report=term --cov-fail-under=90` and ensure all tests pass and coverage remains >90%.

7.  **Commit:**
    *   Stage the changes (`git add .`).
    *   Commit the changes using Conventional Commits (e.g., `feat: replace authlib with pyjwt for token handling`).

**Considerations:**

*   Ensure secret key management remains secure.
*   Verify that error handling for invalid/expired tokens is robust.
*   Double-check algorithm consistency (`HS256`, `RS256`, etc.).
