"""
Configuration settings for MyApp
"""
import os
from pathlib import Path

# Application settings
APP_NAME = "myapp"

# GitHub repository settings (change these to your repo)
GITHUB_OWNER = "rabbularafat"
GITHUB_REPO = "myapp"
GITHUB_RELEASES_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

# Alternative: Direct URL to version file (for checking updates)
VERSION_FILE_URL = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/latest-version.txt"

# Local paths
CONFIG_DIR = Path.home() / ".config" / APP_NAME
LOG_DIR = Path.home() / ".local" / "share" / APP_NAME / "logs"
PID_FILE = Path("/tmp") / f"{APP_NAME}-updater.pid"

# Update settings
CHECK_INTERVAL_HOURS = 1  # How often to check for updates (in hours)
AUTO_UPDATE = True  # Whether to automatically install updates
NOTIFY_ONLY = False  # If True, only notify about updates, don't install

# Package manager settings (for .deb installations)
# USE_APT = False: Download .deb directly from GitHub releases (recommended)
# USE_APT = True: Use apt install (requires APT repository setup)
USE_APT = False
APT_REPO_NAME = APP_NAME

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
