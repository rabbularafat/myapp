# MyApp Control System

This document describes how to control and monitor MyApp, a headless auto-updating application.

## Overview

MyApp runs as a headless (no GUI) application that:
- Launches a Chrome extension on startup
- Auto-updates in the background via a system daemon
- Can be controlled via command line

## Commands

### Run the Application

```bash
# Start MyApp (default command)
myapp

# Or explicitly:
myapp run

# Skip update check on startup:
myapp run --skip-update-check
```

### Check Status

```bash
# Check if MyApp is running
myapp status
```

Output shows:
- Running state (🟢 RUNNING or 🔴 STOPPED)
- Process ID (PID)
- Version
- Device/Host information
- Start timestamp

### Stop the Application

```bash
# Stop running MyApp instance
myapp stop

# Or use Ctrl+C if running in foreground
```

### Manual Update

```bash
# Check for updates
myapp update --check-only

# Install updates
myapp update

# Force reinstall current version
myapp update --force
```

### Version Information

```bash
# Show version info
myapp --version

# Detailed version check (current vs latest)
myapp version-check
```

## Auto-Update Daemon

The daemon runs as a systemd service and automatically checks for updates.

### Daemon Commands

```bash
# Check daemon status
myapp daemon status

# Start daemon
myapp daemon start

# Stop daemon
myapp daemon stop

# Restart daemon
myapp daemon restart

# Run daemon in foreground (for debugging)
myapp daemon start --foreground
```

### Systemd Commands

```bash
# Check daemon status
sudo systemctl status myapp-updater

# View daemon logs
journalctl -u myapp-updater -f

# Restart daemon
sudo systemctl restart myapp-updater

# Stop daemon
sudo systemctl stop myapp-updater
```

## Status Files

MyApp writes status information to files for monitoring:

### For Regular Users
```
~/.myapp/myapp.pid    # Process ID file
~/.myapp/status       # Full status file
```

### For Root/System
```
/var/run/myapp/myapp.pid
/var/run/myapp/status
```

### Status File Format

```
running
version=1.4.0
pid=12345
device=username
host=hostname
timestamp=2026-02-10 12:00:00
```

## Monitoring

### Check if Running

```bash
# Via CLI
myapp status

# Via PID file
cat ~/.myapp/myapp.pid

# Via process list
pgrep -f "myapp.*main.py"
```

### View Logs

```bash
# Daemon logs
journalctl -u myapp-updater -f

# Restart logs (for debugging)
cat /tmp/myapp-restart.log
```

## Configuration

Configuration file: `/etc/myapp/config.env`

```bash
# Update check interval in hours (default: 6)
CHECK_INTERVAL_HOURS=6

# Auto-install updates (default: true)
AUTO_UPDATE=true

# Only notify about updates, don't auto-install (default: false)
NOTIFY_ONLY=false
```

## Troubleshooting

### App Won't Start

1. Check if already running:
   ```bash
   myapp status
   ```

2. Check for stale PID file:
   ```bash
   rm ~/.myapp/myapp.pid
   myapp run
   ```

3. Check logs:
   ```bash
   cat /tmp/myapp-restart.log
   ```

### Updates Not Working

1. Check daemon status:
   ```bash
   sudo systemctl status myapp-updater
   ```

2. Check for update manually:
   ```bash
   myapp update --check-only
   ```

3. View daemon logs:
   ```bash
   journalctl -u myapp-updater -f
   ```

### Chrome Extension Not Opening

1. Ensure Chrome is installed:
   ```bash
   which google-chrome
   ```

2. Check if running as correct user (not root)

3. Check logs for errors

## Architecture

```
┌─────────────────────────────────────────────┐
│                  MyApp                       │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────┐    ┌──────────────────┐   │
│  │  Main App   │    │  Update Daemon   │   │
│  │  (myapp)    │    │  (systemd)       │   │
│  └─────────────┘    └──────────────────┘   │
│        │                    │               │
│        ▼                    ▼               │
│  ┌─────────────┐    ┌──────────────────┐   │
│  │   Chrome    │    │  GitHub Releases │   │
│  │  Extension  │    │  (version check) │   │
│  └─────────────┘    └──────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘

Status Files:
  ~/.myapp/status      - Current app state
  ~/.myapp/myapp.pid   - Process ID

Logs:
  journalctl -u myapp-updater   - Daemon logs
  /tmp/myapp-restart.log        - Restart logs
```
