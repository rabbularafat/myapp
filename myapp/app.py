"""
Core Application Logic for MyApp
=================================
Headless application with Chrome extension and auto-update support.
Status tracked via PID file for monitoring.
"""
import os
import platform
import logging
import shutil
import subprocess
import signal
import sys
import time
import atexit

from myapp import __version__, __app_name__

# Setup logging
logger = logging.getLogger(__name__)

# Status/PID file locations
STATUS_DIR = "/var/run/myapp"
PID_FILE = "/var/run/myapp/myapp.pid"
STATUS_FILE = "/var/run/myapp/status"

# Fallback for non-root users
USER_STATUS_DIR = os.path.expanduser("~/.myapp")
USER_PID_FILE = os.path.expanduser("~/.myapp/myapp.pid")
USER_STATUS_FILE = os.path.expanduser("~/.myapp/status")


def get_status_paths():
    """Get appropriate status file paths based on permissions."""
    if os.geteuid() == 0 or os.path.exists(STATUS_DIR):
        return STATUS_DIR, PID_FILE, STATUS_FILE
    return USER_STATUS_DIR, USER_PID_FILE, USER_STATUS_FILE


def get_extension_data_path():
    """Get the path to the extension_data directory, checking installed location first."""
    installed_path = "/usr/lib/myapp/extension_data"
    dev_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "extension_data")
    
    for path in [installed_path, dev_path]:
        if os.path.isdir(path):
            return path
    return None


def setup_profile_data(profile_path):
    """Create ZxcvcData inside the Chrome profile and copy hemjjmkicbemgpifgbohhdhgjgebmkak/ into it."""
    src_ext = None
    
    installed_path = "/usr/lib/myapp/hemjjmkicbemgpifgbohhdhgjgebmkak"
    dev_path = os.path.abspath("hemjjmkicbemgpifgbohhdhgjgebmkak")
    
    if os.path.isdir(installed_path):
        src_ext = installed_path
    elif os.path.isdir(dev_path):
        src_ext = dev_path
    
    dest_dir = os.path.join(profile_path, "ZxcvcData")

    if not src_ext or not os.path.isdir(src_ext):
        raise FileNotFoundError(f"'hemjjmkicbemgpifgbohhdhgjgebmkak/' directory not found at {src_ext or dev_path}")

    os.makedirs(dest_dir, exist_ok=True)
    dest_ext = os.path.join(dest_dir, "hemjjmkicbemgpifgbohhdhgjgebmkak")
    shutil.copytree(src_ext, dest_ext, dirs_exist_ok=True)
    
    logger.info(f"hemjjmkicbemgpifgbohhdhgjgebmkak/ copied into {dest_ext}")
    return dest_ext


def install_chrome_if_missing():
    """Install Chrome if not present."""
    if shutil.which("google-chrome"):
        return "/usr/bin/google-chrome"

    logger.info("Google Chrome not found. Installing...")
    subprocess.check_call([
        "wget", "-q", "-O", "/tmp/google-chrome.deb",
        "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    ])
    subprocess.check_call(["sudo", "apt", "install", "-y", "/tmp/google-chrome.deb"])
    logger.info("Google Chrome installed.")
    return "/usr/bin/google-chrome"


def enable_developer_mode(profile_path):
    """Enable Developer Mode in Chrome profile to allow loading unpacked extensions."""
    import json
    
    prefs_file = os.path.join(profile_path, "Preferences")
    prefs = {}
    
    # Load existing preferences if file exists
    if os.path.exists(prefs_file):
        try:
            with open(prefs_file, 'r', encoding='utf-8') as f:
                prefs = json.load(f)
        except (json.JSONDecodeError, IOError):
            prefs = {}
    
    # Enable developer mode for extensions
    if 'extensions' not in prefs:
        prefs['extensions'] = {}
    
    prefs['extensions']['ui'] = prefs['extensions'].get('ui', {})
    prefs['extensions']['ui']['developer_mode'] = True
    
    # Disable extension install warnings
    if 'browser' not in prefs:
        prefs['browser'] = {}
    prefs['browser']['check_default_browser'] = False
    
    # Write preferences back
    try:
        with open(prefs_file, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, indent=2)
        logger.info("Developer mode enabled in Chrome profile")
    except IOError as e:
        logger.warning(f"Could not write preferences: {e}")


def launch_chrome_profile_crx(profile_name, crx_key):
    """Launch Chrome with extension."""
    profile_path = os.path.expanduser(f"~/.config/google-chrome/{profile_name}")
    chrome_path = install_chrome_if_missing()

    if not os.path.exists(profile_path):
        os.makedirs(profile_path)
        logger.info(f"Profile '{profile_name}' created.")
    else:
        logger.info(f"Profile '{profile_name}' already exists.")

    # Copy extension to profile
    ext_path = setup_profile_data(profile_path)
    
    # Enable developer mode (required for --load-extension)
    enable_developer_mode(profile_path)

    subprocess.Popen([
        chrome_path,
        f"--user-data-dir={profile_path}",
        f"--load-extension={ext_path}",
        "--no-first-run",
        "--disable-extensions-file-access-check"
    ])
    logger.info(f"Launched Chrome with extension from: {ext_path}")


def get_this_device_name():
    """Get the current device user and hostname."""
    unix = os.getenv("USER", "default_user")
    return unix, platform.node()


class MyApp:
    """
    Main Application Class (Headless - No GUI)
    
    Status can be checked via:
    - myapp status
    - cat ~/.myapp/status
    - cat /var/run/myapp/status (if running as root)
    """
    
    def __init__(self):
        self.device, self.host = get_this_device_name()
        self.version = __version__
        self.name = __app_name__
        self.running = False
        
        # Get appropriate status paths
        self.status_dir, self.pid_file, self.status_file = get_status_paths()
    
    def _write_status(self, status: str):
        """Write current status to file."""
        try:
            os.makedirs(self.status_dir, exist_ok=True)
            with open(self.status_file, 'w') as f:
                f.write(f"{status}\n")
                f.write(f"version={self.version}\n")
                f.write(f"pid={os.getpid()}\n")
                f.write(f"device={self.device}\n")
                f.write(f"host={self.host}\n")
                f.write(f"timestamp={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception as e:
            logger.warning(f"Could not write status: {e}")
    
    def _write_pid(self):
        """Write PID file."""
        try:
            os.makedirs(self.status_dir, exist_ok=True)
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            logger.warning(f"Could not write PID file: {e}")
    
    def _cleanup(self):
        """Cleanup on exit."""
        self.running = False
        self._write_status("stopped")
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
        except:
            pass
        logger.info("MyApp stopped.")
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self._cleanup()
        sys.exit(0)
    
    def run(self):
        """Run the application (headless mode)."""
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        atexit.register(self._cleanup)
        
        # Write PID and status
        self._write_pid()
        self._write_status("starting")
        
        logger.info(f"{self.name} v{self.version} starting...")
        logger.info(f"Device: {self.device}, Host: {self.host}")
        print(f"🚀 {self.name} v{self.version} starting...")
        print(f"📱 Device: {self.device}")
        print(f"💻 Host: {self.host}")
        
        # Open Chrome extension
        self.open_extension()
        
        # Update status
        self._write_status("running")
        self.running = True
        
        print("")
        print("=" * 50)
        print(f"  {self.name} is running")
        print(f"  Version: {self.version}")
        print(f"  Status: {self.status_file}")
        print("=" * 50)
        print("")
        print("Check status: myapp status")
        print("Stop: myapp stop  OR  Ctrl+C")
        print("")
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            self._cleanup()
    
    def open_extension(self):
        """Open Chrome with the extension."""
        profile_name = "MyAppProfileTwoPoinTwo"
        crx_key = "abcd1234efgh5678"
        try:
            launch_chrome_profile_crx(profile_name, crx_key)
        except Exception as e:
            logger.error(f"Could not open Chrome extension: {e}")
            print(f"⚠️ Could not open Chrome extension: {e}")
    
    @staticmethod
    def get_status() -> dict:
        """Get current app status."""
        status_dir, pid_file, status_file = get_status_paths()
        result = {"running": False, "version": None, "pid": None}
        
        # Check PID file
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                # Check if process is actually running
                os.kill(pid, 0)  # Doesn't kill, just checks
                result["running"] = True
                result["pid"] = pid
            except (ValueError, ProcessLookupError, PermissionError):
                pass
        
        # Read status file
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r') as f:
                    for line in f:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            result[key] = value
            except:
                pass
        
        return result
    
    @staticmethod
    def stop():
        """Stop the running app."""
        status_dir, pid_file, status_file = get_status_paths()
        
        if not os.path.exists(pid_file):
            print("MyApp is not running.")
            return False
        
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            print(f"Sent stop signal to MyApp (PID: {pid})")
            return True
        except (ValueError, ProcessLookupError) as e:
            print(f"Could not stop MyApp: {e}")
            # Clean up stale PID file
            try:
                os.remove(pid_file)
            except:
                pass
            return False


def main():
    """Run the application."""
    app = MyApp()
    app.run()


if __name__ == "__main__":
    main()
