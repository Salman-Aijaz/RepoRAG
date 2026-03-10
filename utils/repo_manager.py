"""
📦 Repository Cloning & Cleanup
"""

import os
import stat
import shutil
import tempfile

import git


def clone_repo(repo_url: str) -> str:
    """Shallow-clone a GitHub repo into a temp directory. Returns the path."""
    print(f"🔄 Cloning repository: {repo_url}")
    temp_dir = tempfile.mkdtemp(prefix="repo_")

    try:
        git.Repo.clone_from(repo_url, temp_dir, depth=1)
        print(f"✅ Repository cloned to: {temp_dir}")
        return temp_dir
    except Exception as e:
        force_delete(temp_dir)
        raise RuntimeError(f"Clone failed: {e}")


def force_delete(path: str) -> None:
    """Delete a directory tree, fixing read-only files on Windows."""
    def handle(func, p, _):
        os.chmod(p, stat.S_IWRITE)
        func(p)

    shutil.rmtree(path, onerror=handle, ignore_errors=True)