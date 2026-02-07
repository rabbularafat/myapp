"""
Version comparison utilities
"""
import re
from typing import Tuple, Optional


def parse_version(version_string: str) -> Tuple[int, int, int, int]:
    """
    Parse version string into tuple for comparison.
    Supports formats: 1.0.0, 1.0.0-1, v1.0.0, v1.0.0-1
    
    Returns: (major, minor, patch, release)
    """
    # Remove 'v' prefix if present
    version = version_string.strip().lstrip('v')
    
    # Split by dash to get release number
    parts = version.split('-')
    main_version = parts[0]
    release = int(parts[1]) if len(parts) > 1 else 0
    
    # Parse main version
    version_parts = main_version.split('.')
    major = int(version_parts[0]) if len(version_parts) > 0 else 0
    minor = int(version_parts[1]) if len(version_parts) > 1 else 0
    patch = int(version_parts[2]) if len(version_parts) > 2 else 0
    
    return (major, minor, patch, release)


def compare_versions(current: str, latest: str) -> int:
    """
    Compare two version strings.
    
    Returns:
        -1 if current < latest (update available)
         0 if current == latest (up to date)
         1 if current > latest (current is newer)
    """
    current_tuple = parse_version(current)
    latest_tuple = parse_version(latest)
    
    if current_tuple < latest_tuple:
        return -1
    elif current_tuple > latest_tuple:
        return 1
    return 0


def is_update_available(current: str, latest: str) -> bool:
    """Check if an update is available."""
    return compare_versions(current, latest) < 0


def format_version(major: int, minor: int, patch: int, release: int = 0) -> str:
    """Format version components into a version string."""
    if release > 0:
        return f"{major}.{minor}.{patch}-{release}"
    return f"{major}.{minor}.{patch}"


if __name__ == "__main__":
    # Test version comparison
    test_cases = [
        ("1.0.0", "1.0.1"),
        ("1.0.0", "1.0.0-1"),
        ("1.0.0-1", "1.0.0-2"),
        ("2.0.0", "1.9.9"),
        ("1.0.0", "1.0.0"),
    ]
    
    for current, latest in test_cases:
        result = "UPDATE" if is_update_available(current, latest) else "UP-TO-DATE"
        print(f"{current} vs {latest}: {result}")
