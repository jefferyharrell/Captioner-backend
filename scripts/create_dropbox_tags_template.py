#!/usr/bin/env python3
"""
One-time script to create a Dropbox file properties template for storing photo tags.

- Requires Dropbox OAuth2 access token with 'file_properties.write' scope.
- Run this script from the command line: python create_dropbox_tags_template.py
- The script is idempotent: it will not create a duplicate template if one already
  exists with the same name.

Environment variables required:
    DROPBOX_APP_KEY
    DROPBOX_APP_SECRET
    DROPBOX_REFRESH_TOKEN
    (or a valid access token for manual testing)
"""

import json
import os
import sys

import requests
from dotenv import load_dotenv  # type: ignore[import]  # Added for .env support

# Load environment variables from .env if present
load_dotenv()

DROPBOX_API_URL = "https://api.dropboxapi.com/2/file_properties/templates/add_for_user"
DROPBOX_LIST_TEMPLATES_URL = (
    "https://api.dropboxapi.com/2/file_properties/templates/list_for_user"
)
DROPBOX_TOKEN_URL = "https://api.dropbox.com/oauth2/token"  # noqa: S105

TEMPLATE_NAME = "PhotoTags"
TEMPLATE_DESCRIPTION = "Stores photo tags for Captioner app."
FIELD_NAME = "tags"
FIELD_DESCRIPTION = "Tags for this photo."
FIELD_TYPE = "string"

HTTP_OK = 200
HTTP_CONFLICT = 409
REQUEST_TIMEOUT = 10


def get_access_token() -> str:
    """Get a short-lived access token from Dropbox using refresh token flow."""
    app_key = os.environ.get("DROPBOX_APP_KEY")
    app_secret = os.environ.get("DROPBOX_APP_SECRET")
    refresh_token = os.environ.get("DROPBOX_REFRESH_TOKEN")
    if not (app_key and app_secret and refresh_token):
        print("Missing Dropbox OAuth2 credentials in environment.")  # noqa: T201
        sys.exit(1)
    resp = requests.post(
        DROPBOX_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        auth=(app_key, app_secret),
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code != HTTP_OK:
        print(f"Failed to obtain access token: {resp.text}")  # noqa: T201
        sys.exit(1)
    return resp.json()["access_token"]


def template_exists(token: str, template_name: str) -> str | None:
    resp = requests.post(
        DROPBOX_LIST_TEMPLATES_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        data="null",
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code != HTTP_OK:
        print(f"Failed to list templates: {resp.text}")  # noqa: T201
        sys.exit(1)
    templates = resp.json().get("template_ids", [])
    # Fetch template details to check names
    for tid in templates:
        detail = requests.post(
            "https://api.dropboxapi.com/2/file_properties/templates/get_for_user",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"template_id": tid},
            timeout=REQUEST_TIMEOUT,
        )
        if detail.status_code == HTTP_OK and detail.json().get("name") == template_name:
            print(f"Template '{template_name}' already exists (id: {tid})")  # noqa: T201
            return tid
    return None


def create_template(token: str) -> str | None:
    payload = {
        "name": TEMPLATE_NAME,
        "description": TEMPLATE_DESCRIPTION,
        "fields": [
            {
                "name": FIELD_NAME,
                "description": FIELD_DESCRIPTION,
                "type": FIELD_TYPE,
            }
        ],
    }
    resp = requests.post(
        DROPBOX_API_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload),
        timeout=REQUEST_TIMEOUT,
    )
    if resp.status_code == HTTP_OK:
        tid = resp.json()["template_id"]
        print(f"Created template '{TEMPLATE_NAME}' (id: {tid})")  # noqa: T201
        return tid
    if resp.status_code == HTTP_CONFLICT:
        print(f"Template '{TEMPLATE_NAME}' already exists (409).")  # noqa: T201
        return None
    print(f"Failed to create template: {resp.text}")  # noqa: T201
    sys.exit(1)


def main() -> None:
    token = get_access_token()
    tid = template_exists(token, TEMPLATE_NAME)
    if tid:
        print(f"Template already exists: {tid}")  # noqa: T201
        return
    create_template(token)


if __name__ == "__main__":
    main()
