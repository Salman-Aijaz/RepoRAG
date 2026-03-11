"""
📦 Repository Cloning & Cleanup
Supports both PUBLIC and PRIVATE GitHub repositories.
"""

import os
import stat
import shutil
import tempfile
from urllib.parse import urlparse

import requests
import git


# ── Visibility Check ────────────────────────────────────────────

def is_private_repo(repo_url: str, token: str = None) -> bool:
    """
    Returns True if the repo is private (or if public check fails).
    Uses GitHub API — works with or without a token.
    """
    try:
        # Extract  owner/repo  from URL
        # Handles:
        #   https://github.com/owner/repo
        #   https://github.com/owner/repo.git
        parsed = urlparse(repo_url)
        parts  = parsed.path.strip("/").replace(".git", "").split("/")

        if len(parts) < 2:
            print("⚠️  Could not parse repo URL — assuming public.")
            return False

        owner, repo = parts[0], parts[1]
        api_url     = f"https://api.github.com/repos/{owner}/{repo}"

        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        resp = requests.get(api_url, headers=headers, timeout=10)

        if resp.status_code == 200:
            return resp.json().get("private", False)

        if resp.status_code == 404:
            # 404 without token = private repo (GitHub hides it)
            return True

        print(f"⚠️  GitHub API returned {resp.status_code} — assuming public.")
        return False

    except Exception as e:
        print(f"⚠️  Visibility check failed ({e}) — assuming public.")
        return False


# ── Clone ───────────────────────────────────────────────────────

def _inject_token(repo_url: str, token: str) -> str:
    """
    Turn  https://github.com/owner/repo
    into  https://<token>@github.com/owner/repo
    so git can authenticate without SSH keys.
    """
    parsed   = urlparse(repo_url)
    auth_url = parsed._replace(netloc=f"{token}@{parsed.netloc}")
    return auth_url.geturl()


def clone_repo(repo_url: str, token: str = None) -> str:
    """
    Shallow-clone a repo (public or private) into a temp dir.
    Returns the temp directory path.
    """
    print(f"🔄 Cloning repository: {repo_url}")
    temp_dir   = tempfile.mkdtemp(prefix="repo_")
    clone_url  = _inject_token(repo_url, token) if token else repo_url

    try:
        git.Repo.clone_from(clone_url, temp_dir, depth=1)
        print(f"✅ Repository cloned successfully.")
        return temp_dir
    except Exception as e:
        force_delete(temp_dir)
        raise RuntimeError(f"Clone failed: {e}")


# ── Full Flow ───────────────────────────────────────────────────

def resolve_and_clone(repo_url: str, token: str = None) -> str:
    """
    1. Check if repo is public or private via GitHub API.
    2. If private and no token given → ask user for one.
    3. Clone and return temp dir path.
    """
    print("🔍 Checking repository visibility...")

    private = is_private_repo(repo_url, token)

    if private:
        print("🔒 Repository is PRIVATE.")
        if not token:
            print("\n💡 You need a GitHub Personal Access Token (PAT).")
            print("   How to get one:")
            print("   1. Go to → https://github.com/settings/tokens")
            print("   2. Click 'Generate new token (classic)'")
            print("   3. Give it a name, set expiry")
            print("   4. Under 'Scopes' tick ✅ repo  (top checkbox)")
            print("   5. Click 'Generate token' and COPY it\n")
            token = input("🔑 Paste your GitHub Token here: ").strip()
            if not token:
                raise RuntimeError("❌ Token is required for private repositories.")
    else:
        print("🌐 Repository is PUBLIC — no token needed.")

    return clone_repo(repo_url, token if private else None)


# ── Cleanup ─────────────────────────────────────────────────────

def force_delete(path: str) -> None:
    """Delete a directory tree, fixing read-only files on Windows."""
    def handle(func, p, _):
        os.chmod(p, stat.S_IWRITE)
        func(p)

    shutil.rmtree(path, onerror=handle, ignore_errors=True)