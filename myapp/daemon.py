"""
Update daemon for MyApp
Runs in the background and periodically checks for updates.
"""
import os
import sys
import time
import signal
import logging
import atexit
from pathlib import Path
from datetime import datetime, timedelta

from myapp.config import (
    PID_FILE,
    LOG_DIR,
    CHECK_INTERVAL_HOURS,
    APP_NAME,
)
from myapp.updater import check_and_update

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class UpdateDaemon:
    """Background daemon that periodically checks for updates."""
    
    def __init__(self):
        self.running = False
        self.pid_file = PID_FILE
        self.check_interval = CHECK_INTERVAL_HOURS * 3600  # Convert to seconds
    
    def _get_pid(self) -> int:
        """Get current process ID from pid file."""
        try:
            with open(self.pid_file, 'r') as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return 0
    
    def _write_pid(self):
        """Write current process ID to pid file."""
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
    
    def _remove_pid(self):
        """Remove pid file."""
        try:
            os.unlink(self.pid_file)
        except FileNotFoundError:
            pass
    
    def _is_running(self) -> bool:
        """Check if daemon is already running."""
        pid = self._get_pid()
        if pid == 0:
            return False
        
        try:
            os.kill(pid, 0)  # Check if process exists
            return True
        except OSError:
            # Process doesn't exist, clean up stale pid file
            self._remove_pid()
            return False
    
    def _daemonize(self):
        """
        Daemonize the process using double-fork method.
        Only works on Unix-like systems.
        """
        if sys.platform == 'win32':
            logger.warning("Daemonization not supported on Windows. Running in foreground.")
            return
        
        # First fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            logger.error(f"First fork failed: {e}")
            sys.exit(1)
        
        # Decouple from parent environment
        os.chdir('/')
        os.setsid()
        os.umask(0)
        
        # Second fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            logger.error(f"Second fork failed: {e}")
            sys.exit(1)
        
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        
        with open('/dev/null', 'r') as null_in:
            os.dup2(null_in.fileno(), sys.stdin.fileno())
        
        log_file = LOG_DIR / 'daemon_output.log'
        with open(log_file, 'a+') as log:
            os.dup2(log.fileno(), sys.stdout.fileno())
            os.dup2(log.fileno(), sys.stderr.fileno())
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def start(self, daemon: bool = True):
        """
        Start the update daemon.
        
        Args:
            daemon: If True, fork to background. If False, run in foreground.
        """
        if self._is_running():
            logger.warning(f"Daemon already running with PID {self._get_pid()}")
            return
        
        logger.info(f"Starting {APP_NAME} update daemon...")
        
        if daemon:
            self._daemonize()
        
        # Write PID file
        self._write_pid()
        atexit.register(self._remove_pid)
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        self.running = True
        logger.info(f"Daemon started with PID {os.getpid()}")
        
        # Main loop
        self._run()
    
    def stop(self):
        """Stop the running daemon."""
        pid = self._get_pid()
        
        if pid == 0:
            logger.info("Daemon is not running.")
            return
        
        logger.info(f"Stopping daemon with PID {pid}...")
        
        try:
            os.kill(pid, signal.SIGTERM)
            
            # Wait for process to stop
            for _ in range(30):
                try:
                    os.kill(pid, 0)
                    time.sleep(0.1)
                except OSError:
                    break
            else:
                # Force kill if still running
                os.kill(pid, signal.SIGKILL)
            
            logger.info("Daemon stopped.")
        except OSError as e:
            logger.error(f"Failed to stop daemon: {e}")
        
        self._remove_pid()
    
    def status(self) -> str:
        """Get daemon status."""
        pid = self._get_pid()
        
        if pid == 0:
            return "Daemon is not running."
        
        if self._is_running():
            return f"Daemon is running with PID {pid}."
        else:
            return "Daemon is not running (stale PID file cleaned up)."
    
    def _run(self):
        """Main daemon loop."""
        last_check = datetime.min
        
        while self.running:
            now = datetime.now()
            
            # Check if it's time to check for updates
            if now - last_check >= timedelta(seconds=self.check_interval):
                logger.info("Checking for updates...")
                try:
                    updated = check_and_update(auto_install=True)
                    if updated:
                        logger.info("Update installed successfully!")
                        # Restart the myapp GUI if it's running
                        self._restart_myapp()
                except Exception as e:
                    logger.error(f"Update check failed: {e}")
                
                last_check = now
            
            # Sleep for a bit before next iteration
            time.sleep(60)  # Check every minute if interval has passed
        
        logger.info("Daemon stopped.")
    
    def _restart_myapp(self):
        """Restart the myapp GUI after an update."""
        import subprocess
        import pwd
        
        logger.info("Restarting myapp...")
        
        # Find the actual user (not root) who is running the desktop
        real_user = None
        real_uid = None
        display = None
        
        try:
            # Get the user who owns the display
            result = subprocess.run(
                ["who"],
                capture_output=True,
                text=True
            )
            for line in result.stdout.strip().split('\n'):
                if ':0' in line or 'tty' in line:
                    real_user = line.split()[0]
                    break
            
            if real_user:
                real_uid = pwd.getpwnam(real_user).pw_uid
                display = ":0"
                logger.info(f"Found desktop user: {real_user} (uid={real_uid})")
        except Exception as e:
            logger.warning(f"Could not find desktop user: {e}")
        
        # Send desktop notification
        try:
            env = os.environ.copy()
            if display:
                env['DISPLAY'] = display
            if real_user:
                env['DBUS_SESSION_BUS_ADDRESS'] = f"unix:path=/run/user/{real_uid}/bus"
            
            subprocess.run([
                "notify-send", 
                "MyApp Updated!", 
                "A new version has been installed. Restarting...",
                "-i", "system-software-update"
            ], capture_output=True, timeout=5, env=env)
        except Exception:
            pass
        
        # Kill any running myapp processes (except this daemon)
        try:
            # Find myapp processes
            result = subprocess.run(
                ["pgrep", "-f", "myapp.*main.py"],
                capture_output=True,
                text=True
            )
            pids = result.stdout.strip().split('\n')
            my_pid = str(os.getpid())
            
            for pid in pids:
                pid = pid.strip()
                if pid and pid != my_pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        logger.info(f"Killed old myapp process {pid}")
                    except:
                        pass
        except Exception as e:
            logger.warning(f"Could not kill old processes: {e}")
        
        # Wait a moment
        time.sleep(3)
        
        # Start new myapp instance AS THE USER (not as root)
        try:
            env = os.environ.copy()
            env['DISPLAY'] = display or ':0'
            
            if real_user and real_uid:
                # Run as the actual user
                env['HOME'] = f"/home/{real_user}"
                env['USER'] = real_user
                env['LOGNAME'] = real_user
                env['DBUS_SESSION_BUS_ADDRESS'] = f"unix:path=/run/user/{real_uid}/bus"
                
                # Use sudo to run as user (or su)
                cmd = ["sudo", "-u", real_user, "-E", "/usr/bin/myapp"]
            else:
                cmd = ["/usr/bin/myapp"]
            
            subprocess.Popen(
                cmd,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env
            )
            logger.info(f"Started new myapp instance as user {real_user or 'current'}")
        except Exception as e:
            logger.error(f"Failed to start new myapp: {e}")


def main():
    """Command-line interface for the daemon."""
    import argparse
    
    parser = argparse.ArgumentParser(description=f'{APP_NAME} Update Daemon')
    parser.add_argument(
        'action',
        choices=['start', 'stop', 'restart', 'status', 'run'],
        help='Action to perform'
    )
    parser.add_argument(
        '--foreground', '-f',
        action='store_true',
        help='Run in foreground (don\'t daemonize)'
    )
    
    args = parser.parse_args()
    daemon = UpdateDaemon()
    
    if args.action == 'start':
        daemon.start(daemon=not args.foreground)
    elif args.action == 'stop':
        daemon.stop()
    elif args.action == 'restart':
        daemon.stop()
        time.sleep(1)
        daemon.start(daemon=not args.foreground)
    elif args.action == 'status':
        print(daemon.status())
    elif args.action == 'run':
        # Run in foreground (useful for debugging)
        daemon.start(daemon=False)


if __name__ == "__main__":
    main()
