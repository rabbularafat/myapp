"""
Command-line interface for MyApp
"""
import argparse
import sys

from myapp import __version__, __app_name__
from myapp.updater import Updater, check_and_update
from myapp.daemon import UpdateDaemon


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        prog=__app_name__,
        description='MyApp - A self-updating Python application',
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'{__app_name__} {__version__}'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run command (default)
    run_parser = subparsers.add_parser('run', help='Run the main application')
    run_parser.add_argument(
        '--skip-update-check',
        action='store_true',
        help='Skip checking for updates on startup'
    )
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Check for and install updates')
    update_parser.add_argument(
        '--check-only', '-c',
        action='store_true',
        help='Only check for updates, don\'t install'
    )
    update_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force reinstall even if already on latest version'
    )
    
    # Daemon commands
    daemon_parser = subparsers.add_parser('daemon', help='Manage update daemon')
    daemon_parser.add_argument(
        'action',
        choices=['start', 'stop', 'restart', 'status'],
        help='Daemon action'
    )
    daemon_parser.add_argument(
        '--foreground',
        action='store_true',
        help='Run daemon in foreground'
    )
    
    # Version check command
    version_parser = subparsers.add_parser('version-check', help='Check current and latest versions')
    
    args = parser.parse_args()
    
    # Default to 'run' if no command specified
    if args.command is None:
        args.command = 'run'
        args.skip_update_check = False
    
    if args.command == 'run':
        run_app(skip_update_check=args.skip_update_check)
    elif args.command == 'update':
        handle_update(check_only=args.check_only, force=args.force)
    elif args.command == 'daemon':
        handle_daemon(args.action, foreground=args.foreground)
    elif args.command == 'version-check':
        show_version_info()


def run_app(skip_update_check: bool = False):
    """Run the main application."""
    from myapp.app import MyApp
    
    if not skip_update_check:
        print("📡 Checking for updates...")
        try:
            updater = Updater()
            update_available, latest = updater.check_for_update()
            
            if update_available:
                print(f"⬆️  New version available: {latest}")
                response = input("Would you like to update now? [y/N]: ")
                if response.lower() == 'y':
                    if updater.install_update():
                        print("✅ Update installed! Please restart the application.")
                        sys.exit(0)
            else:
                print("✅ You're running the latest version!")
        except Exception as e:
            print(f"⚠️  Could not check for updates: {e}")
    
    # Run the main application
    app = MyApp()
    
    try:
        app.run()
        
        # Keep running (remove this if your app.run() handles its own loop)
        print("\nPress Ctrl+C to exit.")
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Goodbye update!")


def handle_update(check_only: bool = False, force: bool = False):
    """Handle update command."""
    print(f"📡 Checking for updates (current: v{__version__})...")
    
    updater = Updater()
    update_available, latest = updater.check_for_update()
    
    if update_available or force:
        if update_available:
            print(f"⬆️  New version available: {latest}")
        else:
            print(f"🔄 Force reinstalling version {__version__}...")
        
        if not check_only:
            print("📥 Installing update...")
            if updater.install_update():
                print("✅ Update installed successfully!")
                print("Please restart the application to use the new version.")
            else:
                print("❌ Update failed. Check logs for details.")
                sys.exit(1)
    else:
        print(f"✅ Already on latest version: {__version__}")


def handle_daemon(action: str, foreground: bool = False):
    """Handle daemon commands."""
    daemon = UpdateDaemon()
    
    if action == 'start':
        print("🚀 Starting update daemon...")
        daemon.start(daemon=not foreground)
    elif action == 'stop':
        print("🛑 Stopping update daemon...")
        daemon.stop()
    elif action == 'restart':
        print("🔄 Restarting update daemon...")
        daemon.stop()
        import time
        time.sleep(1)
        daemon.start(daemon=not foreground)
    elif action == 'status':
        print(daemon.status())


def show_version_info():
    """Show detailed version information."""
    print(f"📦 {__app_name__}")
    print(f"   Installed version: {__version__}")
    
    try:
        updater = Updater()
        update_available, latest = updater.check_for_update()
        print(f"   Latest version:    {latest or 'Unknown'}")
        
        if update_available:
            print(f"\n⬆️  Update available! Run '{__app_name__} update' to install.")
        else:
            print("\n✅ You're running the latest version!")
    except Exception as e:
        print(f"   Latest version:    Could not check ({e})")


if __name__ == "__main__":
    main()
