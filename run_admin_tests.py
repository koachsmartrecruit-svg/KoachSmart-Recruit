#!/usr/bin/env python3
"""
Admin Permission Test Runner
Runs comprehensive tests for the admin permission system
"""

import sys
import subprocess
import os
from pathlib import Path

def run_tests():
    """Run admin permission tests"""
    print("🧪 Running KoachSmart Admin Permission Tests")
    print("=" * 50)
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Install pytest if not available
    try:
        import pytest
    except ImportError:
        print("📦 Installing pytest...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest"])
        import pytest
    
    # Run the tests
    test_args = [
        "tests/test_admin_permissions.py",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--color=yes",  # Colored output
    ]
    
    print(f"🚀 Running: pytest {' '.join(test_args)}")
    print("-" * 50)
    
    # Run tests
    exit_code = pytest.main(test_args)
    
    print("-" * 50)
    if exit_code == 0:
        print("✅ All admin permission tests passed!")
        print("\n📊 Test Coverage:")
        print("  ✅ Role-based access control")
        print("  ✅ City access restrictions")
        print("  ✅ Permission validation")
        print("  ✅ Activity logging")
        print("  ✅ API credentials")
        print("  ✅ Admin metrics")
        print("  ✅ Integration workflows")
    else:
        print("❌ Some tests failed. Check output above.")
        print("\n🔧 Common issues:")
        print("  - Database connection problems")
        print("  - Missing dependencies")
        print("  - Configuration issues")
    
    return exit_code


def run_specific_test_class(class_name):
    """Run a specific test class"""
    test_args = [
        f"tests/test_admin_permissions.py::{class_name}",
        "-v",
        "--tb=short",
        "--color=yes",
    ]
    
    print(f"🎯 Running specific test class: {class_name}")
    print("-" * 50)
    
    exit_code = pytest.main(test_args)
    return exit_code


def main():
    """Main test runner"""
    if len(sys.argv) > 1:
        # Run specific test class
        class_name = sys.argv[1]
        return run_specific_test_class(class_name)
    else:
        # Run all tests
        return run_tests()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)