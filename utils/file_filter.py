"""
🔍 File Filtering Logic
"""

from pathlib import Path
from typing import List

from config.settings import (
    INCLUDE_EXTENSIONS,
    INCLUDE_EXACT_NAMES,
    EXCLUDE_FOLDERS,
    SOFT_EXCLUDE_FOLDERS,
)


def should_exclude(path: Path) -> bool:
    """
    Returns True if the file should be skipped.
    - Hard excludes: always skip (node_modules, .git, etc.)
    - Soft excludes: skip dist/build unless it's a config/doc file
    """
    parts = path.parts

    # Hard exclude
    for part in parts:
        if part in EXCLUDE_FOLDERS:
            return True

    # Soft exclude — dist / build folders
    for part in parts:
        if part in SOFT_EXCLUDE_FOLDERS:
            # Keep config/doc files even inside build/dist
            if path.suffix in {'.yml', '.yaml', '.json', '.md', '.txt'}:
                return False
            # Drop minified JS/CSS
            if path.suffix in {'.js', '.css'} and (
                '.min.' in path.name or path.name.endswith('.min.js')
            ):
                return True
            return True

    return False


def filter_files(repo_path: str) -> List[str]:
    """Walk the repo and return paths of all relevant source files."""
    print("🔍 Filtering code files...")
    valid_files: List[str] = []
    skipped = 0

    for path in Path(repo_path).rglob("*"):
        if not path.is_file():
            continue

        if should_exclude(path):
            skipped += 1
            continue

        # Match by extension
        if path.suffix.lower() in INCLUDE_EXTENSIONS:
            valid_files.append(str(path))
            continue

        # Match by exact filename (Dockerfile, Makefile, …)
        if path.name in INCLUDE_EXACT_NAMES:
            valid_files.append(str(path))
            continue

        # Extensionless files whose stem matches (e.g. bare "Makefile")
        if path.stem in INCLUDE_EXACT_NAMES and path.suffix == '':
            valid_files.append(str(path))
            continue

    print(f"✅ Found {len(valid_files)} relevant files (skipped ~{skipped} excluded)")

    # Show root-level picks for quick sanity-check
    root = Path(repo_path)
    root_files = [f for f in valid_files if Path(f).parent == root]
    if root_files:
        print(f"📁 Root-level files included: {[Path(f).name for f in root_files]}")

    return valid_files