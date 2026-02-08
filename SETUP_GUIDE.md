# 🚀 Complete Setup Guide: GitHub to Linux Auto-Update

This guide explains how to set up automatic updates from GitHub to your Linux users.

---

## 📋 Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DEVELOPER (You)                               │
│                                                                       │
│  1. Make code changes                                                │
│  2. git tag v1.1.0                                                   │
│  3. git push origin v1.1.0                                           │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        GITHUB ACTIONS                                 │
│                                                                       │
│  1. Builds .deb package automatically                                │
│  2. Creates GitHub Release with .deb attached                        │
│  3. Updates latest-version.txt in main branch                        │
└───────────────────────────────┬───────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        END USER (Linux)                               │
│                                                                       │
│  First Install:                                                      │
│    wget https://github.com/rabbularafat/myapp/releases/...           │
│    sudo dpkg -i myapp_1.0.0-1_all.deb                                │
│                                                                       │
│  After Install (Automatic):                                          │
│    - Daemon runs every 6 hours                                       │
│    - Checks latest-version.txt on GitHub                             │
│    - Downloads & installs new .deb if available                      │
│    - Sends desktop notification                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Step 1: Push to GitHub

First, create the GitHub repository and push your code:

```bash
# In your project directory (on Windows or Linux)
cd d:\backEnd\app

# Initialize git (if not done)
git init

# Add all files
git add .
git commit -m "Initial commit - MyApp with auto-update"

# Add remote (create repo on GitHub first: github.com/rabbularafat/myapp)
git remote add origin https://github.com/rabbularafat/myapp.git

# Push to main branch
git branch -M main
git push -u origin main
```

---

## 🏷️ Step 2: Create a Release

To trigger the auto-build and create a release:

```bash
# Create version tag
git tag v1.0.0

# Push the tag to GitHub
git push origin v1.0.0
```

**What happens automatically:**
1. GitHub Actions starts
2. Builds `myapp_1.0.0-1_all.deb`
3. Creates Release at: `https://github.com/rabbularafat/myapp/releases/tag/v1.0.0`
4. Updates `latest-version.txt` to `1.0.0`

---

## 🐧 Step 3: Install on Linux (First Time)

On your Linux machine:

```bash
# Download the .deb from GitHub releases
wget https://github.com/rabbularafat/myapp/releases/download/v1.0.0/myapp_1.0.0-1_all.deb

# Install the .deb package
sudo dpkg -i myapp_1.0.0-1_all.deb

# Fix any missing dependencies
sudo apt-get install -f -y

# Verify installation
myapp --version
# Output: myapp 1.0.0

# Check the auto-updater daemon status
systemctl status myapp-updater
```

---

## 🔄 Step 4: Release an Update

When you make changes and want to release a new version:

```bash
# On your development machine (Windows)

# Make your code changes...

# Update version in myapp/__init__.py (optional - workflow does this too)
# __version__ = "1.1.0"

# Commit changes
git add .
git commit -m "New features for v1.1.0"
git push origin main

# Create and push new version tag
git tag v1.1.0
git push origin v1.1.0
```

**On user's Linux machine (happens automatically):**
1. Daemon checks `https://raw.githubusercontent.com/rabbularafat/myapp/main/latest-version.txt`
2. Sees version is `1.1.0` (newer than installed `1.0.0`)
3. Downloads `myapp_1.1.0-1_all.deb` from GitHub releases
4. Installs it with `sudo dpkg -i`
5. Sends desktop notification: "Update installed! Please restart."

---

## ⏰ Automatic Update Schedule

The daemon checks for updates every **1 hours** by default.

To change this, edit `myapp/config.py`:
```python
CHECK_INTERVAL_HOURS = 1  # Change to 1 for hourly, 24 for daily
```

---

## 🛠️ Manual Commands (for users)

```bash
# Check for updates manually
myapp update

# Check without installing
myapp update --check-only

# View version info
myapp version-check

# Daemon control
myapp daemon status
myapp daemon start
myapp daemon stop
myapp daemon restart
```

---

## 📁 Files Created on Linux After Install

```
/usr/bin/myapp              # Main executable
/usr/bin/myapp-daemon       # Daemon executable
/usr/lib/myapp/             # Python package
/etc/myapp/config.env       # Configuration file
/lib/systemd/system/myapp-updater.service  # Systemd service

# User directories (created when app runs):
~/.config/myapp/            # User config
~/.local/share/myapp/logs/  # Log files
```

---

## 🔍 Troubleshooting

### Check daemon logs:
```bash
journalctl -u myapp-updater -f
# or
cat ~/.local/share/myapp/logs/daemon.log
```

### Restart daemon if stuck:
```bash
sudo systemctl restart myapp-updater
```

### Manual update if daemon fails:
```bash
# Download latest
wget https://github.com/rabbularafat/myapp/releases/latest/download/myapp_VERSION_all.deb

# Install
sudo dpkg -i myapp_*.deb
```

---

## ✅ Summary

| Action | Command |
|--------|---------|
| **Create release** | `git tag v1.1.0 && git push origin v1.1.0` |
| **Install on Linux** | `wget ... && sudo dpkg -i myapp_*.deb` |
| **Check updates** | `myapp update --check-only` |
| **Force update** | `myapp update` |
| **Daemon status** | `systemctl status myapp-updater` |

The system is now fully automated:
- **You push a tag** → GitHub builds and releases
- **User installs once** → Auto-updates forever! 🎉

git push 
# 1. Make your changes
# 2. Stage and commit
git add .
git commit -m "your message"
# 3. ALWAYS push to main FIRST!
git push origin main       # ← DON'T FORGET THIS!
# 4. Then create and push tag
git tag v1.2.2
git push origin v1.2.2

wget https://github.com/rabbularafat/myapp/releases/download/v1.2.0/myapp_1.2.0-1_all.deb
sudo dpkg -i myapp_1.2.0-1_all.deb
# Restart the daemon to pick up new code
sudo systemctl restart myapp-updater
# Verify it's running
systemctl status myapp-updater

# remove 
sudo apt remove myapp
sudo dpkg -r myapp
sudo apt purge myapp
sudo dpkg -P myapp
sudo systemctl daemon-reload
dpkg -l | grep myapp