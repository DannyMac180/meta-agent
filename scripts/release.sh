#!/bin/bash
# One-command release script
# Usage: ./scripts/release.sh [patch|minor|major]

set -e

if [ $# -eq 0 ]; then
    echo "Usage: ./scripts/release.sh [patch|minor|major]"
    exit 1
fi

BUMP_TYPE=$1

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Working directory is not clean. Please commit or stash changes first."
    git status --short
    exit 1
fi

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "❌ Not on main branch. Currently on: $CURRENT_BRANCH"
    echo "Please switch to main branch first: git checkout main"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(grep '__version__' src/meta_agent/__about__.py | cut -d'"' -f2)
echo "📋 Current version: $CURRENT_VERSION"

# Bump version
echo "🔄 Bumping $BUMP_TYPE version..."
python scripts/bump_version.py $BUMP_TYPE

# Get new version
NEW_VERSION=$(grep '__version__' src/meta_agent/__about__.py | cut -d'"' -f2)
echo "🆕 New version: $NEW_VERSION"

# Ask for confirmation
read -p "🤔 Release version $NEW_VERSION? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Release cancelled. Reverting version changes..."
    git checkout -- src/meta_agent/__about__.py pyproject.toml
    exit 1
fi

# Commit and push
echo "📝 Committing version bump..."
git add src/meta_agent/__about__.py pyproject.toml
git commit -m "🔖 Bump version to $NEW_VERSION"

echo "🚀 Pushing to trigger release..."
git push origin main

echo "✅ Version $NEW_VERSION pushed to main!"
echo "🔗 Check release progress: https://github.com/DannyMac180/meta-agent/actions"
echo "📦 PyPI package will be available at: https://pypi.org/project/meta-agent-cli/$NEW_VERSION/"
