#!/usr/bin/env python3
"""
Test runner for Hydra News Python components.

This script runs all the tests for the Python components of the Hydra News system.
"""

import os
import sys
import unittest
import argparse

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

def run_tests(test_pattern=None, verbose=False):
    """Run the tests matching the given pattern"""
    # Discover and run tests
    loader = unittest.TestLoader()
    
    if test_pattern:
        # Run specific tests matching the pattern
        suite = loader.loadTestsFromName(test_pattern)
    else:
        # Run all tests in the current directory
        suite = loader.discover(os.path.dirname(__file__))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    # Return the result
    return result.wasSuccessful()

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run Hydra News Python tests')
    parser.add_argument('--pattern', '-p', help='Pattern to match test names')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    # Run the tests
    success = run_tests(args.pattern, args.verbose)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
