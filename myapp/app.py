"""
Core Application Logic for MyApp
=================================
Simple GUI application with auto-update support.
"""
import os
import platform
import logging
import threading

from myapp import __version__, __app_name__

# Setup logging
logger = logging.getLogger(__name__)


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


if __name__ == "__main__":
    main()
