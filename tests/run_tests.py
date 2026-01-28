#!/usr/bin/env python3
"""
Test runner script for Khelo Coach application
"""
import pytest
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_tests():
    """Run all tests with coverage reporting"""
    
    # Test configuration
    pytest_args = [
        '-v',  # Verbose output
        '--tb=short',  # Short traceback format
        '--strict-markers',  # Strict marker checking
        '--disable-warnings',  # Disable warnings for cleaner output
        'tests/',  # Test directory
    ]
    
    # Add coverage if available
    try:
        import pytest_cov
        pytest_args.extend([
            '--cov=.',  # Coverage for all files
            '--cov-report=html:htmlcov',  # HTML coverage report
            '--cov-report=term-missing',  # Terminal coverage report
            '--cov-fail-under=70',  # Fail if coverage below 70%
        ])
        print("Running tests with coverage reporting...")
    except ImportError:
        print("Running tests without coverage (install pytest-cov for coverage)")
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
        if 'pytest_cov' in sys.modules:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n❌ Tests failed with exit code: {exit_code}")
    
    return exit_code


def run_specific_test_file(test_file):
    """Run tests from a specific file"""
    pytest_args = [
        '-v',
        '--tb=short',
        f'tests/{test_file}'
    ]
    
    print(f"Running tests from {test_file}...")
    exit_code = pytest.main(pytest_args)
    return exit_code


def run_test_category(category):
    """Run tests by category"""
    category_map = {
        'auth': 'test_auth.py',
        'profile': 'test_profile.py',
        'jobs': 'test_jobs.py',
        'dashboard': 'test_dashboard.py',
        'resume': 'test_resume_builder.py'
    }
    
    if category in category_map:
        return run_specific_test_file(category_map[category])
    else:
        print(f"Unknown category: {category}")
        print(f"Available categories: {', '.join(category_map.keys())}")
        return 1


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] in ['auth', 'profile', 'jobs', 'dashboard', 'resume']:
            exit_code = run_test_category(sys.argv[1])
        elif sys.argv[1].endswith('.py'):
            exit_code = run_specific_test_file(sys.argv[1])
        else:
            print("Usage:")
            print("  python run_tests.py                    # Run all tests")
            print("  python run_tests.py auth               # Run auth tests")
            print("  python run_tests.py test_auth.py       # Run specific test file")
            exit_code = 1
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code)