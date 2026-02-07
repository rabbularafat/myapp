# MyApp - Auto-Updating Python Application

A complete self-updating Python application with background daemon support for Linux systems.

## 🚀 Features

- **Automatic Updates**: Background daemon checks for updates periodically
- **GitHub Integration**: Fetches latest releases from GitHub API
- **APT Repository Support**: Can be distributed via APT for seamless updates
- **Systemd Service**: Runs as a system service for reliability
- **Cross-Platform Check**: Version checking works anywhere, installation on Linux

## 📦 Project Structure

```
myapp/
├── myapp/
│   ├── __init__.py       # Version info
│   ├── config.py         # Configuration settings
│   ├── version_utils.py  # Version comparison utilities
│   ├── updater.py        # Core update logic
│   ├── daemon.py         # Background update daemon
│   └── cli.py            # Command-line interface
├── scripts/
│   ├── build-deb.sh      # Build .deb package
│   ├── release.sh        # Create GitHub release
│   └── setup-apt-repo.sh # Setup APT repository
├── tests/
│   ├── test_version_utils.py
│   └── test_updater.py
├── .github/
│   └── workflows/
│       └── release.yml   # CI/CD workflow
├── main.py               # Entry point
├── pyproject.toml        # Python project config
├── latest-version.txt    # Version file for update checks
└── README.md
```

## 🔧 Configuration

Edit `myapp/config.py` to customize:

```python
# Your GitHub repository
GITHUB_OWNER = "your-username"
GITHUB_REPO = "myapp"

# Update settings
CHECK_INTERVAL_HOURS = 6  # How often to check
AUTO_UPDATE = True        # Auto-install updates
```

## 💻 Usage

### As a User

```bash
# Run the application
myapp

# Check for updates manually
myapp update

# Check without installing
myapp update --check-only

# Manage the background daemon
myapp daemon start
myapp daemon stop
myapp daemon status

# View version info
myapp --version
myapp version-check
```

### As a Developer

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Build .deb package
./scripts/build-deb.sh 1.0.0

# Create a release
./scripts/release.sh 1.0.0

# Setup APT repository
./scripts/setup-apt-repo.sh
```

## 🔄 How Auto-Update Works

### Update Flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  User's System  │────▶│  GitHub/Server   │────▶│  Check Version  │
│  (myapp-daemon) │     │ (latest-version) │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Install Update  │◀────│ Update Available│
                        │  (via APT/.deb)  │     │      Check      │
                        └──────────────────┘     └─────────────────┘
```

### Components

1. **Version File** (`latest-version.txt`): Hosted on GitHub, contains latest version
2. **Updater Module**: Compares versions, downloads and installs updates
3. **Daemon**: Runs in background, periodically checks for updates
4. **Systemd Service**: Ensures daemon starts on boot

## 📋 Distribution Methods

### Method 1: GitHub Releases (Recommended)

1. **Create Release**:
   ```bash
   ./scripts/release.sh 1.0.0
   ```

2. **User Installation**:
   ```bash
   # Download .deb from GitHub releases
   wget https://github.com/user/myapp/releases/latest/download/myapp_1.0.0-1_all.deb
   sudo dpkg -i myapp_1.0.0-1_all.deb
   ```

3. **Auto-Updates**: The installed daemon checks GitHub for new releases

### Method 2: APT Repository

1. **Setup Repository**:
   ```bash
   ./scripts/setup-apt-repo.sh
   # Deploy apt-repo/ to GitHub Pages or web server
   ```

2. **User Installation**:
   ```bash
   # Add repository
   echo "deb [trusted=yes] https://user.github.io/myapp-repo stable main" | \
       sudo tee /etc/apt/sources.list.d/myapp.list
   
   # Install
   sudo apt update
   sudo apt install myapp
   ```

3. **Auto-Updates**: Updates via `apt upgrade` or daemon

## 🔐 Security Considerations

- The daemon runs as root to install packages via APT
- Consider using signed packages for production
- Version file should be on HTTPS
- Validate downloaded packages before installation

## 📝 Release Checklist

1. ✅ Update version in `myapp/__init__.py`
2. ✅ Update version in `pyproject.toml`
3. ✅ Build .deb: `./scripts/build-deb.sh X.Y.Z`
4. ✅ Test locally: `sudo dpkg -i dist/myapp_X.Y.Z-1_all.deb`
5. ✅ Create release: `./scripts/release.sh X.Y.Z`
6. ✅ Update `latest-version.txt` on main branch
7. ✅ Update APT repo if using: `./scripts/setup-apt-repo.sh`

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request
