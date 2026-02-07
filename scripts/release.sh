#!/bin/bash
# =========================================================
# GitHub Release Script for MyApp
# =========================================================
# This script creates a new release on GitHub with the .deb
# package attached.
#
# Prerequisites:
#   - GitHub CLI (gh) installed and authenticated
#   - .deb package already built
#
# Usage:
#   ./scripts/release.sh VERSION [RELEASE_NOTES]
#   Example: ./scripts/release.sh 1.0.0 "Initial release"
# =========================================================

set -e

# Configuration
APP_NAME="myapp"
VERSION="${1}"
RELEASE_NOTES="${2:-Release v${VERSION}}"

if [ -z "$VERSION" ]; then
    echo "❌ Error: Version is required"
    echo "Usage: $0 VERSION [RELEASE_NOTES]"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEB_FILE="${PROJECT_ROOT}/dist/${APP_NAME}_${VERSION}-1_all.deb"

echo "🚀 Releasing ${APP_NAME} v${VERSION}"
echo "================================================"

# Check if .deb exists
if [ ! -f "$DEB_FILE" ]; then
    echo "⚠️  .deb file not found. Building..."
    "${SCRIPT_DIR}/build-deb.sh" "${VERSION}"
fi

# Update version in source files
echo "📝 Updating version in source files..."

# Update __init__.py
sed -i "s/__version__ = \".*\"/__version__ = \"${VERSION}\"/" "${PROJECT_ROOT}/myapp/__init__.py"

# Update pyproject.toml
sed -i "s/version = \".*\"/version = \"${VERSION}\"/" "${PROJECT_ROOT}/pyproject.toml"

# Update latest-version.txt
echo "$VERSION" > "${PROJECT_ROOT}/latest-version.txt"

echo "📄 Committing version changes..."
git add .
git commit -m "Release v${VERSION}" || true

echo "🏷️  Creating git tag..."
git tag -a "v${VERSION}" -m "Release v${VERSION}" || true
git push origin main --tags || true

echo "📦 Creating GitHub release..."
gh release create "v${VERSION}" \
    --title "v${VERSION}" \
    --notes "${RELEASE_NOTES}" \
    "${DEB_FILE}"

echo ""
echo "✅ Release v${VERSION} created successfully!"
echo "   https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/releases/tag/v${VERSION}"
