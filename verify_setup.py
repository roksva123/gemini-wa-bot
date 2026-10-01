#!/usr/bin/env python3
"""
Setup Verification Script
Checks if testing framework is ready to use
"""

import sys
import subprocess
import os
from pathlib import Path
import json

class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

def check(description, condition):
    """Print check result"""
    if condition:
        print(f"{Color.GREEN}✓{Color.RESET} {description}")
        return True
    else:
        print(f"{Color.RED}✗{Color.RESET} {description}")
        return False

def main():
    print(f"\n{Color.BLUE}WhatsApp Bot Testing Framework - Setup Verification{Color.RESET}\n")

    checks_passed = 0
    checks_total = 0

    # 1. Check Python
    print("1️⃣  Python Environment")
    checks_total += 1
    try:
        version = subprocess.check_output([sys.executable, "--version"], text=True).strip()
        if check("Python installed", version):
            checks_passed += 1
    except:
        check("Python installed", False)

    # 2. Check required files
    print("\n2️⃣  Required Files")
    required_files = [
        "test_cases.yaml",
        "demo_test_runner.py",
        "TESTING_FRAMEWORK.md",
        "DEMO_TEST_README.md",
        "requirements_demo.txt",
    ]

    for file in required_files:
        checks_total += 1
        if check(f"  {file}", Path(file).exists()):
            checks_passed += 1

    # 3. Check templates
    print("\n3️⃣  Test Templates")
    templates = [
        "test_templates/test_cases.phone_repair.yaml",
        "test_templates/test_cases.ecommerce.yaml",
    ]

    for template in templates:
        checks_total += 1
        if check(f"  {template}", Path(template).exists()):
            checks_passed += 1

    # 4. Check quick start scripts
    print("\n4️⃣  Quick Start Scripts")
    scripts = [
        ("quick_demo.bat", "Windows"),
        ("quick_demo.sh", "Linux/Mac"),
        ("quickstart.py", "Interactive"),
    ]

    for script, platform in scripts:
        checks_total += 1
        if check(f"  {script} ({platform})", Path(script).exists()):
            checks_passed += 1

    # 5. Check dependencies
    print("\n5️⃣  Python Dependencies")
    dependencies = ["yaml", "httpx"]

    for dep in dependencies:
        checks_total += 1
        try:
            __import__(dep)
            check(f"  {dep}", True)
            checks_passed += 1
        except ImportError:
            check(f"  {dep} (install with: pip install pyyaml httpx)", False)

    # 6. Check bot API
    print("\n6️⃣  Bot API")
    checks_total += 1
    try:
        import httpx
        response = httpx.get("http://localhost:8000/health", timeout=2)
        if check("Bot running at http://localhost:8000", response.status_code == 200):
            checks_passed += 1
        else:
            check("Bot running at http://localhost:8000", False)
    except:
        check("Bot running at http://localhost:8000 (start with: python main.py)", False)

    # 7. Check test case format
    print("\n7️⃣  Test Case Format")
    checks_total += 1
    try:
        import yaml
        with open("test_cases.yaml") as f:
            config = yaml.safe_load(f)

        has_business_info = "business_info" in config
        has_test_cases = "test_cases" in config
        num_cases = len(config.get("test_cases", []))

        if has_business_info and has_test_cases and num_cases > 0:
            check(f"Test cases valid ({num_cases} cases found)", True)
            checks_passed += 1
        else:
            check("Test cases valid", False)
    except Exception as e:
        check(f"Test cases valid (error: {e})", False)

    # Summary
    print(f"\n{'─' * 60}")
    print(f"\n📊 Summary: {checks_passed}/{checks_total} checks passed\n")

    if checks_passed == checks_total:
        print(f"{Color.GREEN}✓ Everything looks good! Ready to use.{Color.RESET}\n")
        print("Next steps:")
        print("  1. Edit test_cases.yaml with your business info")
        print("  2. Run: python demo_test_runner.py")
        print("  3. Open test_report.html in browser")
        print("  4. Share report with client\n")
        return 0
    else:
        missing = checks_total - checks_passed
        print(f"{Color.YELLOW}⚠  {missing} issue(s) found.{Color.RESET}\n")
        print("Fix:")
        print("  • Install dependencies: pip install pyyaml httpx")
        print("  • Start bot: python main.py")
        print("  • Or run quick start: quick_demo.bat (Windows) or bash quick_demo.sh (Linux/Mac)\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
