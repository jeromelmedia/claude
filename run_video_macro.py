#!/usr/bin/env python3
"""
Launcher script that automatically handles dependencies and runs the video macro.
No virtual environment activation needed - just run this!
"""

import subprocess
import sys
import os
from pathlib import Path

def check_and_install_package(package_name, import_name=None):
    """Check if a package is installed, install if not."""
    if import_name is None:
        import_name = package_name

    try:
        __import__(import_name)
        return True
    except ImportError:
        print(f"Installing {package_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "--user", "--quiet"])
            print(f"✓ {package_name} installed")
            return True
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package_name}")
            return False

def main():
    """Main launcher function."""
    print("=" * 60)
    print("AI VIDEO GENERATION MACRO - AUTO LAUNCHER")
    print("=" * 60)

    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8 or higher is required")
        sys.exit(1)

    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # Required packages
    packages = [
        ("anthropic", "anthropic"),
        ("selenium", "selenium"),
        ("requests", "requests"),
        ("pillow", "PIL"),
        ("pydub", "pydub"),
        ("pyautogui", "pyautogui"),
        ("webdriver-manager", "webdriver_manager"),
    ]

    print("\nChecking dependencies...")
    all_installed = True

    for package, import_name in packages:
        try:
            __import__(import_name)
            print(f"✓ {package}")
        except ImportError:
            print(f"⚠ {package} not found, installing...")
            if not check_and_install_package(package, import_name):
                all_installed = False

    if not all_installed:
        print("\n✗ Some packages failed to install. Please run manually:")
        print(f"  {sys.executable} -m pip install anthropic selenium requests pillow pydub pyautogui webdriver-manager")
        sys.exit(1)

    print("\n✓ All dependencies installed!")
    print("\nStarting video generation macro...\n")
    print("=" * 60)

    # Import and run the main script
    try:
        # Add current directory to path
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir))

        # Import and run the macro
        from ai_video_generation_macro import main as run_macro
        run_macro()

    except Exception as e:
        print(f"\n✗ Error running macro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
