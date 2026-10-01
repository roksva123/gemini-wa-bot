#!/usr/bin/env python3
"""
Quick Start Setup untuk Demo Test Runner
Jalankan script ini untuk setup awal dan coba test pertama kali
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command"""
    print(f"\n📌 {description}")
    print(f"   Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=False)
    return result.returncode == 0

def main():
    print("""
╔════════════════════════════════════════════════════════════════╗
║       WhatsApp Bot Demo Test Runner - Quick Setup             ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: main.py not found. Please run from bot root directory.")
        sys.exit(1)

    # Install dependencies
    print("\n1️⃣  Installing dependencies...")
    if not run_command("pip install -r requirements_demo.txt", "Install test runner dependencies"):
        print("⚠️  Warning: Could not install all dependencies")

    # Check if bot is running
    print("\n2️⃣  Checking if bot is running...")
    result = subprocess.run(
        "python -c \"import httpx; httpx.get('http://localhost:8000/health', timeout=2)\"",
        shell=True,
        capture_output=True
    )

    if result.returncode != 0:
        print("⚠️  Bot is not running at http://localhost:8000")
        print("   Start it with: python main.py")
        print("\n   Then run this script again, or run tests manually:")
        print("   python demo_test_runner.py")
        return

    print("✅ Bot is running!")

    # Show test cases
    print("\n3️⃣  Test cases configured:")
    print("   Run: python demo_test_runner.py")
    print("   OR with custom settings:")
    print("   python demo_test_runner.py --api http://localhost:8000 --phone 628123456789")

    # Ask to run tests
    print("\n4️⃣  Ready to run tests?")
    answer = input("   Run tests now? (y/n): ").strip().lower()

    if answer == 'y':
        print("\n🚀 Starting tests...\n")
        subprocess.run("python demo_test_runner.py")

        print("""
╔════════════════════════════════════════════════════════════════╗
║                     ✅ Test Complete!                         ║
╚════════════════════════════════════════════════════════════════╝

📊 Reports generated:
   • test_report.html  - Open in browser for visual report
   • test_report.json  - Raw data for integration

💡 Next steps:
   1. Edit test_cases.yaml to customize for your business
   2. Run tests again: python demo_test_runner.py
   3. Share test_report.html with clients/stakeholders
        """)

        # Try to open HTML report
        try:
            import webbrowser
            webbrowser.open('test_report.html')
        except:
            pass

if __name__ == "__main__":
    main()
