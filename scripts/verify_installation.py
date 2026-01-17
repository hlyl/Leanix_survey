#!/usr/bin/env python3
"""
Installation verification script for LeanIX Survey Creator.
Run this after installation to verify everything is set up correctly.
"""

import importlib.util
import sys
from pathlib import Path


def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 12:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} - Need 3.12+")
        return False


def check_module(module_name):
    """Check if a module is installed"""
    spec = importlib.util.find_spec(module_name)
    if spec is not None:
        print(f"✓ {module_name} - Installed")
        return True
    else:
        print(f"✗ {module_name} - Missing")
        return False


def check_files():
    """Check if all required files exist"""
    print("\nChecking project files...")

    required_files = [
        "leanix_survey_models.py",
        "streamlit_app.py",
        "api.py",
        "validate_survey.py",
        "pyproject.toml",
        "requirements.txt",
        "README.md",
        "example_survey_simple.json",
    ]

    all_present = True
    for file in required_files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - Missing")
            all_present = False

    return all_present


def check_dependencies():
    """Check if all dependencies are installed"""
    print("\nChecking dependencies...")

    dependencies = [
        "pydantic",
        "fastapi",
        "uvicorn",
        "httpx",
        "streamlit",
    ]

    all_installed = True
    for dep in dependencies:
        if not check_module(dep):
            all_installed = False

    return all_installed


def check_examples():
    """Validate example files"""
    print("\nValidating example files...")

    try:
        import json

        from leanix_survey_models import SurveyInput

        examples = [
            "example_survey_simple.json",
            "example_survey_comprehensive.json",
            "example_survey_factsheet_mapping.json",
        ]

        all_valid = True
        for example in examples:
            if not Path(example).exists():
                print(f"✗ {example} - File not found")
                all_valid = False
                continue

            try:
                with open(example) as f:
                    data = json.load(f)
                survey = SurveyInput.model_validate(data)
                print(f"✓ {example} - Valid ('{survey.title}')")
            except Exception as e:
                print(f"✗ {example} - Invalid: {str(e)}")
                all_valid = False

        return all_valid

    except ImportError as e:
        print(f"✗ Cannot validate - Missing dependency: {e}")
        return False


def main():
    """Run all checks"""
    print("=" * 60)
    print("LeanIX Survey Creator - Installation Verification")
    print("=" * 60)

    checks = []

    # Python version
    checks.append(("Python Version", check_python_version()))

    # Files
    checks.append(("Project Files", check_files()))

    # Dependencies
    checks.append(("Dependencies", check_dependencies()))

    # Examples
    checks.append(("Example Validation", check_examples()))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:.<40} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 Installation verified successfully!")
        print("\nNext steps:")
        print("  1. Run: streamlit run streamlit_app.py")
        print("  2. Or validate a survey: python validate_survey.py example_survey_simple.json")
        print("  3. Read QUICKSTART.md for more information")
        return 0
    else:
        print("\n⚠️  Installation incomplete!")
        print("\nTo fix:")
        print("  1. Make sure you're in the project directory")
        print("  2. Activate virtual environment: source .venv/bin/activate")
        print("  3. Install dependencies: uv pip install -e .")
        print("  4. Run this script again")
        return 1


if __name__ == "__main__":
    sys.exit(main())
