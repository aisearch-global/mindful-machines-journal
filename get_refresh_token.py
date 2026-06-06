"""
get_refresh_token.py — One-time OAuth2 setup for Blogger API.

Run this LOCALLY (not in CI) to get the refresh token you'll store as
GOOGLE_REFRESH_TOKEN in your GitHub Actions secrets.

Usage:
    pip install google-auth-oauthlib
    python get_refresh_token.py

You'll need:
  - GOOGLE_CLIENT_ID  (from Google Cloud Console → OAuth 2.0 credentials)
  - GOOGLE_CLIENT_SECRET

Set them as environment variables before running, or paste them when prompted.
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/blogger"]

def main():
    client_id = os.environ.get("GOOGLE_CLIENT_ID") or input("Paste your Google Client ID: ").strip()
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET") or input("Paste your Google Client Secret: ").strip()

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n" + "=" * 60)
    print("SUCCESS — save these as GitHub Actions secrets:")
    print("=" * 60)
    print(f"GOOGLE_CLIENT_ID     = {client_id}")
    print(f"GOOGLE_CLIENT_SECRET = {client_secret}")
    print(f"GOOGLE_REFRESH_TOKEN = {creds.refresh_token}")
    print("=" * 60)
    print("\nAlso set:")
    print("  ANTHROPIC_API_KEY  — your Anthropic API key")
    print("  BLOGGER_BLOG_ID    — numeric ID from your Blogger dashboard URL")

if __name__ == "__main__":
    main()
