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
        import glob
        
        logger.info("Restarting myapp...")
        
        # Find the actual user (not root) who is running the desktop
        real_user = None
        real_uid = None
        display = ":0"
        xauthority = None
        
        try:
            # Method 1: Use loginctl to find sessions (most reliable)
            result = subprocess.run(
                ["loginctl", "list-sessions", "--no-legend"],
                capture_output=True,
                text=True
            )
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 3:
                    session_id = parts[0]
                    # Check if this session has a display
                    session_info = subprocess.run(
                        ["loginctl", "show-session", session_id, "-p", "Type", "-p", "User", "-p", "Name"],
                        capture_output=True,
                        text=True
                    )
                    if 'Type=x11' in session_info.stdout or 'Type=wayland' in session_info.stdout:
                        for info_line in session_info.stdout.split('\n'):
                            # Try to get Name first (actual username)
                            if info_line.startswith('Name='):
                                real_user = info_line.split('=')[1].strip()
                            # User= gives UID, convert it
                            elif info_line.startswith('User=') and not real_user:
                                try:
                                    uid = int(info_line.split('=')[1].strip())
                                    user_info = pwd.getpwuid(uid)
                                    real_user = user_info.pw_name
                                    real_uid = uid
                                except:
                                    pass
                    if real_user:
                        break
            
            # Method 2: Check /run/user directories
            if not real_user:
                for user_dir in glob.glob('/run/user/*'):
                    try:
                        uid = int(os.path.basename(user_dir))
                        if uid >= 1000:  # Regular users start at 1000
                            user_info = pwd.getpwuid(uid)
                            real_user = user_info.pw_name
                            real_uid = uid
                            logger.info(f"Found user from /run/user: {real_user} (uid={real_uid})")
                            break
                    except:
                        continue
            
            # Method 3: Find owner of the X display
            if not real_user:
                result = subprocess.run(
                    ["stat", "-c", "%U", "/tmp/.X11-unix/X0"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    real_user = result.stdout.strip()
            
            # Get full user info if we have a username but not uid
            if real_user and real_user != 'root' and not real_uid:
                try:
                    user_info = pwd.getpwnam(real_user)
                    real_uid = user_info.pw_uid
                except Exception as e:
                    logger.warning(f"Could not get uid for '{real_user}': {e}")
            
            # Find Xauthority if we have user info
            if real_user and real_uid:
                xauth_paths = [
                    f"/home/{real_user}/.Xauthority",
                    f"/run/user/{real_uid}/gdm/Xauthority",
                ]
                # Also check for wayland auth files
                for pattern in [f"/run/user/{real_uid}/.mutter-Xwaylandauth.*"]:
                    xauth_paths.extend(glob.glob(pattern))
                
                for path in xauth_paths:
                    if os.path.exists(path):
                        xauthority = path
                        break
                logger.info(f"Found desktop user: {real_user} (uid={real_uid})")
                
        except Exception as e:
            logger.warning(f"Could not find desktop user: {e}")
        
        # Send desktop notification
        try:
            notify_env = os.environ.copy()
            notify_env['DISPLAY'] = display
            if real_uid:
                notify_env['DBUS_SESSION_BUS_ADDRESS'] = f"unix:path=/run/user/{real_uid}/bus"
            
            subprocess.run([
                "notify-send", 
                "MyApp Updated!", 
                "A new version has been installed. Restarting...",
                "-i", "system-software-update"
            ], capture_output=True, timeout=5, env=notify_env)
        except Exception:
            pass
        
        # Kill any running myapp processes (except this daemon)
        try:
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
        
        # Wait for old process to fully exit
        time.sleep(3)
        
        # Start new myapp instance
        if real_user and real_uid:
            # Build the command that will be run as the user
            # We need to export the display environment INSIDE the user's shell
            xauth_export = f"XAUTHORITY={xauthority}" if xauthority else "XAUTHORITY=/home/{real_user}/.Xauthority"
            dbus_export = f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{real_uid}/bus"
            
            # Log file for debugging
            log_file = "/tmp/myapp-restart.log"
            
            # Allow local X connections (needed for tkinter)
            try:
                subprocess.run(["xhost", "+local:"], capture_output=True, timeout=5,
                              env={'DISPLAY': display})
            except:
                pass
            
            # The actual command to run - export all needed env vars in bash
            # Use nohup and & to run in background
            inner_cmd = f"export DISPLAY={display}; export {dbus_export}; export HOME=/home/{real_user}; export USER={real_user}; export {xauth_export}; "
            # Use 'run --no-gui' to skip tkinter GUI but still open Chrome extension
            inner_cmd += f"nohup /usr/bin/myapp run --no-gui >> {log_file} 2>&1 &"
            
            logger.info(f"Restart command: {inner_cmd}")
            
            # Try multiple methods to start as user
            methods = [
                # Method 1: runuser with bash -c
                ["runuser", "-u", real_user, "--", "bash", "-c", inner_cmd],
                # Method 2: sudo with bash -c  
                ["sudo", "-u", real_user, "bash", "-c", inner_cmd],
                # Method 3: su with bash
                ["su", "-", real_user, "-c", inner_cmd],
            ]
            
            for i, cmd in enumerate(methods):
                try:
                    logger.info(f"Trying method {i+1}: {cmd[0]} ...")
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        timeout=10,
                        cwd=f"/home/{real_user}"
                    )
                    
                    # Since we use nohup ... &, bash exits immediately with code 0
                    # Wait a moment then check if myapp is running
                    time.sleep(2)
                    
                    # Check if myapp process is now running
                    check = subprocess.run(
                        ["pgrep", "-f", "myapp.*main.py"],
                        capture_output=True,
                        text=True
                    )
                    
                    if check.returncode == 0 and check.stdout.strip():
                        logger.info(f"Started myapp successfully with method {i+1} (pid: {check.stdout.strip()})")
                        return
                    else:
                        full_output = result.stdout.decode() + result.stderr.decode()
                        logger.warning(f"Method {i+1}: bash exited but myapp not running. Output: {full_output[:200]}")
                        
                except subprocess.TimeoutExpired:
                    logger.warning(f"Method {i+1}: timeout")
                except Exception as e:
                    logger.warning(f"Method {i+1} error: {e}")
                    continue
            
            logger.error("All restart methods failed!")
        else:
            # Fallback: try direct execution
            try:
                subprocess.Popen(
                    ["/usr/bin/myapp"],
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info("Started myapp (fallback method)")
            except Exception as e:
                logger.error(f"Fallback restart failed: {e}")


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
