"""
Auto-updater module for MyApp
Handles checking for updates and installing them.
"""
import json
import logging
import subprocess
import sys
import os
import tempfile
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from myapp import __version__
from myapp.config import (
    GITHUB_RELEASES_URL,
    VERSION_FILE_URL,
    APP_NAME,
    USE_APT,
    APT_REPO_NAME,
    LOG_DIR,
    AUTO_UPDATE,
    NOTIFY_ONLY,
)
from myapp.version_utils import is_update_available, parse_version

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UpdateError(Exception):
    """Custom exception for update errors."""
    pass


class Updater:
    """Handles checking and installing updates."""
    
    def __init__(self, use_github_releases: bool = False):
        """
        Initialize the updater.
        
        Args:
            use_github_releases: If True, check GitHub releases API (has rate limits!).
                                If False, check VERSION_FILE_URL (recommended).
        """
        self.current_version = __version__
        self.use_github_releases = use_github_releases
        self.latest_version: Optional[str] = None
        self.download_url: Optional[str] = None
        self.release_notes: Optional[str] = None
    
    def check_for_update(self) -> Tuple[bool, Optional[str]]:
        """
        Check if an update is available.
        
        Returns:
            Tuple of (update_available: bool, latest_version: str or None)
        """
        try:
            if self.use_github_releases:
                return self._check_github_releases()
            else:
                return self._check_version_file()
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            return False, None
    
    def _check_github_releases(self) -> Tuple[bool, Optional[str]]:
        """Check GitHub releases API for latest version."""
        try:
            request = urllib.request.Request(
                GITHUB_RELEASES_URL,
                headers={'User-Agent': f'{APP_NAME}/{self.current_version}'}
            )
            
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            self.latest_version = data.get('tag_name', '').lstrip('v')
            self.release_notes = data.get('body', '')
            
            # Find .deb asset for download
            assets = data.get('assets', [])
            for asset in assets:
                if asset['name'].endswith('.deb'):
                    self.download_url = asset['browser_download_url']
                    break
            
            update_available = is_update_available(self.current_version, self.latest_version)
            
            if update_available:
                logger.info(f"Update available: {self.current_version} -> {self.latest_version}")
            else:
                logger.info(f"Already on latest version: {self.current_version}")
            
            return update_available, self.latest_version
            
        except urllib.error.URLError as e:
            logger.error(f"Network error checking GitHub releases: {e}")
            raise UpdateError(f"Network error: {e}")
    
    def _check_version_file(self) -> Tuple[bool, Optional[str]]:
        """Check version file URL for latest version (no rate limits!)."""
        try:
            request = urllib.request.Request(
                VERSION_FILE_URL,
                headers={'User-Agent': f'{APP_NAME}/{self.current_version}'}
            )
            
            with urllib.request.urlopen(request, timeout=10) as response:
                self.latest_version = response.read().decode('utf-8').strip()
            
            # Construct download URL from version
            # Format: https://github.com/OWNER/REPO/releases/download/vX.X.X/myapp_X.X.X-1_all.deb
            from myapp.config import GITHUB_OWNER, GITHUB_REPO
            self.download_url = (
                f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/"
                f"v{self.latest_version}/{APP_NAME}_{self.latest_version}-1_all.deb"
            )
            
            update_available = is_update_available(self.current_version, self.latest_version)
            
            if update_available:
                logger.info(f"Update available: {self.current_version} -> {self.latest_version}")
            else:
                logger.info(f"Already on latest version: {self.current_version}")
            
            return update_available, self.latest_version
            
        except urllib.error.URLError as e:
            logger.error(f"Network error checking version file: {e}")
            raise UpdateError(f"Network error: {e}")
    
    def install_update(self) -> bool:
        """
        Install the latest update.
        
        Returns:
            True if update was successful, False otherwise.
        """
        if not self.latest_version:
            logger.error("No update information available. Call check_for_update() first.")
            return False
        
        if NOTIFY_ONLY:
            logger.info(f"Update {self.latest_version} available but NOTIFY_ONLY is set.")
            self._send_notification(
                "Update Available",
                f"Version {self.latest_version} is available. Please update manually."
            )
            return False
        
        try:
            if USE_APT:
                return self._install_via_apt()
            else:
                return self._install_via_deb()
        except Exception as e:
            logger.error(f"Failed to install update: {e}")
            return False
    
    def _install_via_apt(self) -> bool:
        """Install update using APT package manager."""
        logger.info("Installing update via APT...")
        
        try:
            # Update package lists
            result = subprocess.run(
                ["sudo", "apt-get", "update"],
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode != 0:
                logger.error(f"APT update failed: {result.stderr}")
                return False
            
            # Install/upgrade package
            result = subprocess.run(
                ["sudo", "apt-get", "install", "-y", APT_REPO_NAME],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                logger.error(f"APT install failed: {result.stderr}")
                return False
            
            logger.info("Update installed successfully via APT!")
            self._send_notification(
                "Update Installed",
                f"Successfully updated to version {self.latest_version}. Please restart the application."
            )
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("APT command timed out")
            return False
        except subprocess.SubprocessError as e:
            logger.error(f"Subprocess error: {e}")
            return False
    
    def _install_via_deb(self) -> bool:
        """Download and install .deb package directly."""
        if not self.download_url:
            logger.error("No .deb download URL available")
            return False
        
        logger.info(f"Downloading .deb from {self.download_url}...")
        
        try:
            # Download to temp file
            with tempfile.NamedTemporaryFile(suffix='.deb', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                
                request = urllib.request.Request(
                    self.download_url,
                    headers={'User-Agent': f'{APP_NAME}/{self.current_version}'}
                )
                
                with urllib.request.urlopen(request, timeout=300) as response:
                    tmp_file.write(response.read())
            
            # Install .deb package
            logger.info(f"Installing .deb package from {tmp_path}...")
            result = subprocess.run(
                ["sudo", "dpkg", "-i", tmp_path],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Fix dependencies if needed
            if result.returncode != 0:
                logger.warning("dpkg install had issues, attempting to fix dependencies...")
                subprocess.run(
                    ["sudo", "apt-get", "install", "-f", "-y"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
            
            # Cleanup
            os.unlink(tmp_path)
            
            logger.info("Update installed successfully!")
            self._send_notification(
                "Update Installed",
                f"Successfully updated to version {self.latest_version}. Please restart the application."
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to install .deb: {e}")
            return False
    
    def _send_notification(self, title: str, message: str):
        """Send desktop notification (Linux)."""
        try:
            subprocess.run(
                ["notify-send", title, message, "-i", "system-software-update"],
                capture_output=True,
                timeout=5
            )
        except Exception:
            # Notification is optional, don't fail if it doesn't work
            pass


def check_and_update(auto_install: bool = AUTO_UPDATE) -> bool:
    """
    Convenience function to check for updates and optionally install them.
    
    Args:
        auto_install: If True, automatically install available updates.
        
    Returns:
        True if an update was installed, False otherwise.
    """
    updater = Updater()
    
    update_available, latest_version = updater.check_for_update()
    
    if update_available and auto_install:
        return updater.install_update()
    
    return False


if __name__ == "__main__":
    # Test the updater
    print(f"Current version: {__version__}")
    
    updater = Updater(use_github_releases=False)
    update_available, latest = updater.check_for_update()
    
    if update_available:
        print(f"Update available: {latest}")
        response = input("Install update? [y/N]: ")
        if response.lower() == 'y':
            updater.install_update()
    else:
        print("Already on latest version!")
