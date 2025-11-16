#!/usr/bin/env python3
"""
Setup Verification Script
Checks that all dependencies are installed and configured correctly
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Check Python version is 3.10+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        return False, f"Python {version.major}.{version.minor} (need 3.10+)"
    return True, f"Python {version.major}.{version.minor}.{version.micro}"


def check_package_installed(package_name):
    """Check if a Python package is installed"""
    try:
        __import__(package_name)
        return True, "Installed"
    except ImportError:
        return False, "Not installed"


def check_file_exists(filepath):
    """Check if a file exists"""
    path = Path(filepath)
    if path.exists():
        size = path.stat().st_size
        size_mb = size / (1024 * 1024)
        return True, f"Found ({size_mb:.1f} MB)"
    return False, "Not found"


def main():
    print("=" * 60)
    print("Tamagotchi Chatbot - Setup Verification")
    print("=" * 60)
    print()

    checks = []

    # Python version
    status, info = check_python_version()
    checks.append(("Python Version", status, info))

    # Core dependencies
    packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("sqlalchemy", "SQLAlchemy"),
        ("pydantic", "Pydantic"),
        ("llama_cpp", "llama-cpp-python"),
    ]

    for import_name, display_name in packages:
        status, info = check_package_installed(import_name)
        checks.append((display_name, status, info))

    # Optional dependencies
    optional_packages = [
        ("chromadb", "ChromaDB (optional)"),
    ]

    for import_name, display_name in optional_packages:
        status, info = check_package_installed(import_name)
        checks.append((display_name, status, info))

    # Configuration files
    config_files = [
        ".env",
        "requirements.txt",
        "main.py",
    ]

    for filename in config_files:
        status, info = check_file_exists(filename)
        checks.append((f"File: {filename}", status, info))

    # Directories
    directories = [
        "models",
        "data",
        "logs",
    ]

    for dirname in directories:
        status, info = check_file_exists(dirname)
        checks.append((f"Directory: {dirname}", status, info))

    # Model file check
    if os.path.exists(".env"):
        # Try to load .env and check MODEL_PATH
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("MODEL_PATH="):
                        model_path = line.split("=", 1)[1].strip()
                        status, info = check_file_exists(model_path)
                        checks.append(("LLM Model", status, info))
                        break
        except Exception as e:
            checks.append(("LLM Model", False, f"Error reading .env: {e}"))
    else:
        checks.append(("LLM Model", False, ".env not found"))

    # Print results
    print(f"{'Component':<30} {'Status':<12} {'Details':<30}")
    print("-" * 60)

    all_passed = True
    for name, status, info in checks:
        status_str = "✓ PASS" if status else "✗ FAIL"
        status_color = "\033[92m" if status else "\033[91m"
        reset_color = "\033[0m"

        print(f"{name:<30} {status_color}{status_str:<12}{reset_color} {info:<30}")

        if not status and "optional" not in name.lower():
            all_passed = False

    print()
    print("=" * 60)

    if all_passed:
        print("\033[92m✓ All checks passed! Backend is ready to run.\033[0m")
        print()
        print("To start the backend:")
        print("  python main.py")
        print()
        return 0
    else:
        print("\033[91m✗ Some checks failed. Please fix the issues above.\033[0m")
        print()
        print("Common fixes:")
        print("  - Missing packages: pip install -r requirements.txt")
        print("  - Missing .env: cp .env.example .env")
        print("  - Missing model: ./scripts/download_model.sh")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
