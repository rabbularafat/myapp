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



def setup_profile_data(profile_path):
    """
    Create ZxcvcData inside the Chrome profile and copy scripts/ into it.
    """
    src_scripts = os.path.abspath("scripts")
    dest_dir = os.path.join(profile_path, "ZxcvcData")

    if not os.path.isdir(src_scripts):
        raise FileNotFoundError(f"'scripts/' directory not found at {src_scripts}")

    # Create ZxcvcData if missing
    os.makedirs(dest_dir, exist_ok=True)

    # Copy scripts/* → ZxcvcData/
    for item in os.listdir(src_scripts):
        src = os.path.join(src_scripts, item)
        dst = os.path.join(dest_dir, item)

        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    print(f"✅ scripts/ copied into {dest_dir}")

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
        """Main application entry point - launches GUI."""
        print(f"🚀 {self.name} v{self.version} starting...")
        print(f"📱 Device: {self.device}")
        print(f"💻 Host: {self.host}")
        
        # Launch the GUI
        self._create_gui()
    
    def open_extension(self):
        profile_name = "MyAppProfile"
        crx_key = "abcd1234efgh5678"
        launch_chrome_profile_crx(profile_name, crx_key)



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
    app.run()
    app.open_extension()


if __name__ == "__main__":
    main()
