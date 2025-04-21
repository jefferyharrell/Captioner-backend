#!/usr/bin/env python3
"""
Script to generate a Dropbox OAuth2 refresh token for the Captioner app.

- Loads Dropbox app credentials from .env (or environment variables).
- Guides the user through the OAuth2 authorization flow in the browser.
- Prints the resulting refresh token to stdout for use in .env.

Required in .env or environment:
    DROPBOX_APP_KEY
    DROPBOX_APP_SECRET
    DROPBOX_REDIRECT_URI (e.g., http://localhost:8080/)

Scopes required (enable in Dropbox App Console):
    files.metadata.write
    files.metadata.read
    files.content.read

Usage:
    python get_dropbox_refresh_token.py
"""

import os
import sys
import webbrowser
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv  # type: ignore[import]

load_dotenv()

APP_KEY = os.environ.get("DROPBOX_APP_KEY")
APP_SECRET = os.environ.get("DROPBOX_APP_SECRET")
REDIRECT_URI = os.environ.get("DROPBOX_REDIRECT_URI")
SCOPES = [
    "files.metadata.write",
    "files.metadata.read",
    "files.content.read",
]
HTTP_OK = 200
REQUEST_TIMEOUT = 10

if not (APP_KEY and APP_SECRET and REDIRECT_URI):
    print(  # noqa: T201
        "Missing required environment variables: "
        "DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REDIRECT_URI"
    )
    sys.exit(1)

auth_url = "https://www.dropbox.com/oauth2/authorize?" + urlencode(
    {
        "client_id": APP_KEY,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "token_access_type": "offline",
        "scope": " ".join(SCOPES),
    }
)

print("\n1. Open the following URL in your browser and authorize the app:")  # noqa: T201
print(auth_url)  # noqa: T201
webbrowser.open(auth_url)

print("\n2. After authorizing, you will be redirected to your redirect URI.")  # noqa: T201
print("   Copy the 'code' parameter from the URL and paste it below.\n")  # noqa: T201
code = input("Paste the code here: ").strip()

# Exchange code for refresh token
resp = requests.post(
    "https://api.dropboxapi.com/oauth2/token",
    data={
        "code": code,
        "grant_type": "authorization_code",
        "client_id": APP_KEY,
        "client_secret": APP_SECRET,
        "redirect_uri": REDIRECT_URI,
    },
    timeout=REQUEST_TIMEOUT,
)
if resp.status_code != HTTP_OK:
    print(f"Failed to obtain refresh token: {resp.text}")  # noqa: T201
    sys.exit(1)

data = resp.json()
refresh_token = data.get("refresh_token")
if not refresh_token:
    print(f"No refresh token found in response: {data}")  # noqa: T201
    sys.exit(1)

print("\nYour Dropbox refresh token (add to your .env as DROPBOX_REFRESH_TOKEN):\n")  # noqa: T201
print(refresh_token)  # noqa: T201
