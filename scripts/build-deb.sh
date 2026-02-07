#!/bin/bash
# =========================================================
# Debian Package Build Script for MyApp
# =========================================================
# This script creates a .deb package for distribution
# 
# Prerequisites:
#   - dpkg-deb (comes with dpkg)
#   - Python 3.8+
#
# Usage:
#   ./scripts/build-deb.sh [version]
#   Example: ./scripts/build-deb.sh 1.0.0
# =========================================================

set -e

# Configuration
APP_NAME="myapp"
VERSION="${1:-1.0.0}"
RELEASE="${2:-1}"
ARCH="all"
MAINTAINER="Your Name <you@example.com>"
DESCRIPTION="A self-updating Python application with GUI and daemon support"
DEPENDS="python3 (>= 3.8), python3-tk"

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${PROJECT_ROOT}/build/deb"
PACKAGE_NAME="${APP_NAME}_${VERSION}-${RELEASE}_${ARCH}"
PACKAGE_DIR="${BUILD_DIR}/${PACKAGE_NAME}"

echo "🔨 Building ${APP_NAME} v${VERSION}-${RELEASE}"
echo "================================================"

# Clean up previous builds
rm -rf "${BUILD_DIR}"
mkdir -p "${PACKAGE_DIR}"

# Create directory structure
mkdir -p "${PACKAGE_DIR}/DEBIAN"
mkdir -p "${PACKAGE_DIR}/usr/bin"
mkdir -p "${PACKAGE_DIR}/usr/lib/${APP_NAME}"
mkdir -p "${PACKAGE_DIR}/etc/${APP_NAME}"
mkdir -p "${PACKAGE_DIR}/lib/systemd/system"
mkdir -p "${PACKAGE_DIR}/etc/apt/sources.list.d"

echo "📁 Creating package structure..."

# Copy Python package
cp -r "${PROJECT_ROOT}/myapp" "${PACKAGE_DIR}/usr/lib/${APP_NAME}/"
cp "${PROJECT_ROOT}/main.py" "${PACKAGE_DIR}/usr/lib/${APP_NAME}/"

# Create executable wrapper
cat > "${PACKAGE_DIR}/usr/bin/${APP_NAME}" << 'EOF'
#!/bin/bash
PYTHONPATH="/usr/lib/myapp:${PYTHONPATH}" python3 /usr/lib/myapp/main.py "$@"
EOF
chmod +x "${PACKAGE_DIR}/usr/bin/${APP_NAME}"

# Create daemon wrapper
cat > "${PACKAGE_DIR}/usr/bin/${APP_NAME}-daemon" << 'EOF'
#!/bin/bash
PYTHONPATH="/usr/lib/myapp:${PYTHONPATH}" python3 -m myapp.daemon "$@"
EOF
chmod +x "${PACKAGE_DIR}/usr/bin/${APP_NAME}-daemon"

# Create systemd service file
cat > "${PACKAGE_DIR}/lib/systemd/system/${APP_NAME}-updater.service" << EOF
[Unit]
Description=${APP_NAME} Auto-Updater Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/${APP_NAME}-daemon run
Restart=on-failure
RestartSec=30
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Create default config (will not overwrite existing)
cat > "${PACKAGE_DIR}/etc/${APP_NAME}/config.env" << EOF
# MyApp Configuration
# Uncomment and modify values as needed

# Update check interval in hours (default: 6)
# CHECK_INTERVAL_HOURS=6

# Auto-install updates (default: true)
# AUTO_UPDATE=true

# Only notify about updates, don't auto-install (default: false)
# NOTIFY_ONLY=false
EOF

echo "📝 Creating DEBIAN control files..."

# Create control file
cat > "${PACKAGE_DIR}/DEBIAN/control" << EOF
Package: ${APP_NAME}
Version: ${VERSION}-${RELEASE}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: ${DEPENDS}
Maintainer: ${MAINTAINER}
Description: ${DESCRIPTION}
 This package includes a background daemon that automatically
 checks for and installs updates from the configured repository.
EOF

# Create postinst script (runs after installation)
cat > "${PACKAGE_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Reload systemd to recognize new service
systemctl daemon-reload

# Enable and start the updater service
systemctl enable myapp-updater.service
systemctl start myapp-updater.service || true

echo ""
echo "============================================"
echo "  MyApp installed successfully!"
echo "============================================"
echo ""
echo "  Run 'myapp' to start the application"
echo "  Run 'myapp --help' for more options"
echo ""
echo "  The auto-updater daemon has been started."
echo "  Status: systemctl status myapp-updater"
echo ""

exit 0
EOF
chmod +x "${PACKAGE_DIR}/DEBIAN/postinst"

# Create prerm script (runs before removal)
cat > "${PACKAGE_DIR}/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

# Stop and disable the updater service
systemctl stop myapp-updater.service || true
systemctl disable myapp-updater.service || true

exit 0
EOF
chmod +x "${PACKAGE_DIR}/DEBIAN/prerm"

# Create postrm script (runs after removal)
cat > "${PACKAGE_DIR}/DEBIAN/postrm" << 'EOF'
#!/bin/bash
set -e

# Reload systemd
systemctl daemon-reload

# Clean up logs and runtime files
if [ "$1" = "purge" ]; then
    rm -rf /var/log/myapp
    rm -rf /tmp/myapp-*
fi

exit 0
EOF
chmod +x "${PACKAGE_DIR}/DEBIAN/postrm"

# Create conffiles (config files that should be preserved on upgrade)
cat > "${PACKAGE_DIR}/DEBIAN/conffiles" << EOF
/etc/${APP_NAME}/config.env
EOF

echo "📦 Building .deb package..."

# Build the package
dpkg-deb --build "${PACKAGE_DIR}"

# Move to dist directory
mkdir -p "${PROJECT_ROOT}/dist"
mv "${BUILD_DIR}/${PACKAGE_NAME}.deb" "${PROJECT_ROOT}/dist/"

echo ""
echo "✅ Package built successfully!"
echo "   Output: dist/${PACKAGE_NAME}.deb"
echo ""
echo "📋 Package info:"
dpkg-deb --info "${PROJECT_ROOT}/dist/${PACKAGE_NAME}.deb"
