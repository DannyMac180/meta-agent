#!/usr/bin/env python3
"""
Script to bump the version in both pyproject.toml and __about__.py
Usage: python scripts/bump_version.py [major|minor|patch] [--dry-run]
"""

import re
import sys
from pathlib import Path
from typing import Tuple

def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse semantic version string into tuple of integers."""
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-.*)?$', version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")
    return tuple(map(int, match.groups()))

def bump_version(version: str, part: str) -> str:
    """Bump the specified part of the version."""
    major, minor, patch = parse_version(version)
    
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid part: {part}. Must be 'major', 'minor', or 'patch'")
    
    return f"{major}.{minor}.{patch}"

def update_version_files(new_version: str, dry_run: bool = False):
    """Update version in both files."""
    root = Path(__file__).parent.parent
    about_file = root / "src" / "meta_agent" / "__about__.py"
    pyproject_file = root / "pyproject.toml"
    
    # Update __about__.py
    about_content = about_file.read_text()
    new_about = re.sub(
        r'__version__ = "[^"]*"',
        f'__version__ = "{new_version}"',
        about_content
    )
    
    # Update pyproject.toml
    pyproject_content = pyproject_file.read_text()
    new_pyproject = re.sub(
        r'version = "[^"]*"',
        f'version = "{new_version}"',
        pyproject_content
    )
    
    if dry_run:
        print(f"Would update version to {new_version}")
        print(f"__about__.py: {about_file}")
        print(f"pyproject.toml: {pyproject_file}")
    else:
        about_file.write_text(new_about)
        pyproject_file.write_text(new_pyproject)
        print(f"Updated version to {new_version}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/bump_version.py [major|minor|patch] [--dry-run]")
        sys.exit(1)
    
    part = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    
    # Get current version from __about__.py
    root = Path(__file__).parent.parent
    about_file = root / "src" / "meta_agent" / "__about__.py"
    about_content = about_file.read_text()
    
    version_match = re.search(r'__version__ = "([^"]*)"', about_content)
    if not version_match:
        print("Could not find version in __about__.py")
        sys.exit(1)
    
    current_version = version_match.group(1)
    new_version = bump_version(current_version, part)
    
    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")
    
    update_version_files(new_version, dry_run)

if __name__ == "__main__":
    main()
