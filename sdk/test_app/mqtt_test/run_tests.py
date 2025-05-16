#!/usr/bin/env python3
"""
Test runner for the MQTT Test Application.

This script runs the unit and integration tests for the MQTT Test Application
and generates a coverage report.
"""

import os
import sys
import unittest
import coverage
import argparse

def run_tests(test_type="all", verbose=False):
    """
    Run the tests.

    Args:
        test_type: Type of tests to run ("unit", "integration", or "all")
        verbose: Whether to show verbose output

    Returns:
        True if all tests passed, False otherwise
    """
    # Start coverage
    cov = coverage.Coverage(
        source=["test_app.mqtt_test.server", "test_app.mqtt_test.client", "test_app.mqtt_test.config"],
        omit=["*/__init__.py", "*/tests/*"]
    )
    cov.start()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add tests to the suite
    if test_type in ["unit", "all"]:
        unit_tests = loader.discover("tests/unit", pattern="test_*.py")
        suite.addTests(unit_tests)

    if test_type in ["integration", "all"]:
        integration_tests = loader.discover("tests/integration", pattern="test_*.py")
        suite.addTests(integration_tests)

    # Run the tests
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Stop coverage and generate report
    cov.stop()
    cov.save()

    # Print coverage report
    print("\nCoverage Report:")
    cov.report()

    # Generate HTML report
    html_dir = os.path.join(os.path.dirname(__file__), "coverage_html")
    cov.html_report(directory=html_dir)
    print(f"\nHTML coverage report generated in {html_dir}")

    return result.wasSuccessful()

def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run tests for the MQTT Test Application")
    parser.add_argument("--type", choices=["unit", "integration", "all"], default="all",
                        help="Type of tests to run (default: all)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show verbose output")
    args = parser.parse_args()

    # Run the tests
    success = run_tests(args.type, args.verbose)

    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
