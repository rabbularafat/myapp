"""
Core Application Logic for MyApp
=================================
This is where you write your main application functionality.
The updater and daemon are separate from this core logic.
"""
import os
import platform
import logging

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
    Main Application Class
    ----------------------
    Add your application logic here.
    """
    
    def __init__(self):
        self.device, self.host = get_this_device_name()
        self.version = __version__
        self.name = __app_name__
    
    def run(self):
        """Main application entry point."""
        print(f"🚀 {self.name} v{self.version} starting...")
        print(f"📱 Device: {self.device}")
        print(f"💻 Host: {self.host}")
        print("")
        print("=" * 50)
        print("  Your application is running!")
        print("=" * 50)
        print("")
        
        # ================================================
        # ADD YOUR MAIN APPLICATION LOGIC HERE
        # ================================================
        
        self.main_logic()
    
    def main_logic(self):
        """
        Your main application logic goes here.
        This is where you implement your actual functionality.
        """
        # Example: Print device info
        thisDevice, thisDeviceHost = get_this_device_name()
        print(f"thisDevice: {thisDevice}")
        print(f"thisDeviceHost: {thisDeviceHost}")
        
        # TODO: Add your actual application logic below
        # Examples:
        # - Connect to a database
        # - Start a web server
        # - Process files
        # - Run a GUI
        # - etc.
        
        print("\n📝 Add your custom logic in myapp/app.py -> main_logic()")


def main():
    """Run the application."""
    app = MyApp()
    app.run()


if __name__ == "__main__":
    main()
