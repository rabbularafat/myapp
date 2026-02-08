# Extension Data Directory

This directory contains data files that will be copied to the Chrome profile's `ZxcvcData/` folder.

## How it works:
1. When MyApp starts, it looks for this `extension_data/` directory
2. Contents are copied to `~/.config/google-chrome/MyAppProfile/ZxcvcData/`
3. Your Chrome extension can then access these files

## Add your files here:
- Place any scripts, configs, or data files that your extension needs
- They will be automatically synced when the app starts

## Location when installed:
- `/usr/lib/myapp/extension_data/` (on Linux via .deb)
