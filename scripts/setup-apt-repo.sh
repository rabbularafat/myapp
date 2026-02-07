#!/bin/bash
# =========================================================
# Setup APT Repository Script
# =========================================================
# This script sets up a local APT repository structure that
# can be hosted on GitHub Pages, a web server, or served
# locally for testing.
#
# Usage:
#   ./scripts/setup-apt-repo.sh
# =========================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPO_DIR="${PROJECT_ROOT}/apt-repo"
DIST="stable"
COMPONENT="main"
ARCH="all"

echo "📦 Setting up APT repository structure..."
echo "================================================"

# Create repository structure
mkdir -p "${REPO_DIR}/dists/${DIST}/${COMPONENT}/binary-${ARCH}"
mkdir -p "${REPO_DIR}/pool/${COMPONENT}"

# Copy .deb files to pool
echo "📁 Copying packages to pool..."
for deb in "${PROJECT_ROOT}/dist"/*.deb; do
    if [ -f "$deb" ]; then
        cp "$deb" "${REPO_DIR}/pool/${COMPONENT}/"
        echo "   - $(basename "$deb")"
    fi
done

# Generate Packages file
echo "📝 Generating Packages file..."
cd "${REPO_DIR}"
dpkg-scanpackages --arch "${ARCH}" pool/ > "dists/${DIST}/${COMPONENT}/binary-${ARCH}/Packages"
gzip -k -f "dists/${DIST}/${COMPONENT}/binary-${ARCH}/Packages"

# Calculate package counts and sizes
PACKAGE_COUNT=$(grep -c "^Package:" "dists/${DIST}/${COMPONENT}/binary-${ARCH}/Packages" || echo 0)
PACKAGES_SIZE=$(wc -c < "dists/${DIST}/${COMPONENT}/binary-${ARCH}/Packages")
PACKAGES_GZ_SIZE=$(wc -c < "dists/${DIST}/${COMPONENT}/binary-${ARCH}/Packages.gz")
PACKAGES_MD5=$(md5sum "dists/${DIST}/${COMPONENT}/binary-${ARCH}/Packages" | cut -d' ' -f1)
PACKAGES_GZ_MD5=$(md5sum "dists/${DIST}/${COMPONENT}/binary-${ARCH}/Packages.gz" | cut -d' ' -f1)
PACKAGES_SHA256=$(sha256sum "dists/${DIST}/${COMPONENT}/binary-${ARCH}/Packages" | cut -d' ' -f1)
PACKAGES_GZ_SHA256=$(sha256sum "dists/${DIST}/${COMPONENT}/binary-${ARCH}/Packages.gz" | cut -d' ' -f1)

# Generate Release file
echo "📝 Generating Release file..."
cat > "dists/${DIST}/Release" << EOF
Origin: MyApp Repository
Label: MyApp
Suite: ${DIST}
Codename: ${DIST}
Version: 1.0
Architectures: ${ARCH}
Components: ${COMPONENT}
Description: MyApp APT Repository
Date: $(date -Ru)
MD5Sum:
 ${PACKAGES_MD5} ${PACKAGES_SIZE} ${COMPONENT}/binary-${ARCH}/Packages
 ${PACKAGES_GZ_MD5} ${PACKAGES_GZ_SIZE} ${COMPONENT}/binary-${ARCH}/Packages.gz
SHA256:
 ${PACKAGES_SHA256} ${PACKAGES_SIZE} ${COMPONENT}/binary-${ARCH}/Packages
 ${PACKAGES_GZ_SHA256} ${PACKAGES_GZ_SIZE} ${COMPONENT}/binary-${ARCH}/Packages.gz
EOF

# Create installation instructions
cat > "${REPO_DIR}/INSTALL.md" << 'EOF'
# Installing MyApp from APT Repository

## Option 1: GitHub-hosted repository

Add the repository to your system:

```bash
# Add GPG key (if signed)
# wget -qO - https://your-username.github.io/myapp-repo/KEY.gpg | sudo apt-key add -

# Add repository
echo "deb [trusted=yes] https://your-username.github.io/myapp-repo stable main" | \
    sudo tee /etc/apt/sources.list.d/myapp.list

# Update and install
sudo apt update
sudo apt install myapp
```

## Option 2: Local repository (for testing)

```bash
# Add local repository
echo "deb [trusted=yes] file:/path/to/apt-repo stable main" | \
    sudo tee /etc/apt/sources.list.d/myapp-local.list

# Update and install
sudo apt update
sudo apt install myapp
```

## Verify installation

```bash
myapp --version
systemctl status myapp-updater
```
EOF

echo ""
echo "✅ APT repository created successfully!"
echo "   Location: ${REPO_DIR}"
echo ""
echo "📋 Repository contents:"
find "${REPO_DIR}" -type f | head -20
echo ""
echo "📖 To host this repository:"
echo "   1. Push the 'apt-repo' folder to GitHub Pages"
echo "   2. Or serve it on any web server"
echo "   3. See ${REPO_DIR}/INSTALL.md for installation instructions"
