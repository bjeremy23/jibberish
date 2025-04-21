#!/usr/bin/env python
"""
Test runner for Jibberish shell tests using standard Python unittest.
This avoids the dependencies required by PyATS.
"""

import os
import sys
import unittest
import importlib.util
import argparse

def load_test_module(file_path):
    """Load a test module from file path."""
    module_name = os.path.basename(file_path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def collect_tests(test_dir=None):
    """Collect test cases from test files."""
    if test_dir is None:
        # Get the directory this script is in
        test_dir = os.path.dirname(os.path.abspath(__file__))
    
    test_suite = unittest.TestSuite()
    
    # Helper function to add tests from a module
    def add_tests_from_module(module):
        has_unittest_tests = False
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and obj != unittest.TestCase:
                test_suite.addTest(unittest.makeSuite(obj))
                has_unittest_tests = True
        return has_unittest_tests
    
    # Convert PyATS tests to unittest tests
    def convert_pyats_test_to_unittest(module):
        # For each class that inherits from aetest.Testcase
        has_pyats_tests = False
        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and hasattr(obj, '__name__') and not name.startswith('__'):
                # Check if it's a PyATS testcase
                if 'Testcase' in name or 'TestCase' in name:
                    # Skip if this is already a unittest TestCase
                    if issubclass(obj, unittest.TestCase):
                        continue
                    
                    # Create a unittest TestCase equivalent
                    class UnittestWrapper(unittest.TestCase):
                        pass
                    
                    # Find test methods (those with @aetest.test decorator)
                    for method_name in dir(obj):
                        if method_name.startswith('test_'):
                            method = getattr(obj, method_name)
                            # Add the test method to our wrapper class
                            setattr(UnittestWrapper, method_name, method)
                    
                    # Add the wrapper class to our test suite if it has test methods
                    if any(m.startswith('test_') for m in dir(UnittestWrapper)):
                        test_suite.addTest(unittest.makeSuite(UnittestWrapper))
                        has_pyats_tests = True
        return has_pyats_tests
    
    # Walk through all test directories
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    # Try to load the module
                    module = load_test_module(file_path)
                    
                    # First try to add unittest tests
                    has_unittest = add_tests_from_module(module)
                    
                    # Only convert PyATS tests if there are no unittest tests
                    # to avoid double-counting
                    if not has_unittest:
                        convert_pyats_test_to_unittest(module)
                    
                except Exception as e:
                    print(f"Error loading tests from {file_path}: {e}")
    
    return test_suite

def main():
    parser = argparse.ArgumentParser(description='Run tests for Jibberish shell')
    parser.add_argument('test_path', nargs='?', default=None, 
                      help='Path to specific test file or directory')
    parser.add_argument('-m', '--method', 
                      help='Run specific test method (format: TestClass.test_method or just test_method)')
    parser.add_argument('-v', '--verbose', action='store_true',
                      help='Increase output verbosity')
    parser.add_argument('-d', '--debug', action='store_true',
                      help='Print debug information during test discovery')
    args = parser.parse_args()
    
    # Add the project root to the path so that imports work properly
    # This is crucial for proper test discovery, especially for executor tests
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, project_root)
    
    if args.debug:
        print(f"Added {project_root} to Python path")
    
    verbosity = 2 if args.verbose else 1
    
    # Create a test runner
    runner = unittest.TextTestRunner(verbosity=verbosity)
    
    # Determine the test directory/file
    test_path = args.test_path
    if test_path is None:
        # Default: run all tests in the tests directory
        test_path = os.path.dirname(os.path.abspath(__file__))
    
    # If a specific file is provided, run just that file
    if os.path.isfile(test_path) and test_path.endswith('.py'):
        try:
            module = load_test_module(test_path)
            suite = unittest.TestSuite()
            
            # If a method is specified, run only that method
            if args.method:
                # Check if class.method format was provided
                if '.' in args.method:
                    class_name, method_name = args.method.split('.')
                    # Find the test class
                    test_class = None
                    for name in dir(module):
                        obj = getattr(module, name)
                        if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and name == class_name:
                            test_class = obj
                            break
                    
                    if test_class:
                        suite.addTest(test_class(method_name))
                    else:
                        print(f"Error: Test class '{class_name}' not found in {test_path}")
                        sys.exit(1)
                else:
                    # Method name only - look for it in all test classes
                    method_name = args.method
                    found = False
                    for name in dir(module):
                        obj = getattr(module, name)
                        if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and obj != unittest.TestCase:
                            for test_method in [m for m in dir(obj) if m.startswith('test_')]:
                                if test_method == method_name:
                                    suite.addTest(obj(test_method))
                                    found = True
                    
                    if not found:
                        print(f"Error: Test method '{method_name}' not found in {test_path}")
                        sys.exit(1)
            else:
                # Add all test classes from the module
                for name in dir(module):
                    obj = getattr(module, name)
                    if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and obj != unittest.TestCase:
                        suite.addTest(unittest.makeSuite(obj))
            
            if not suite.countTestCases():
                print(f"No tests found in {test_path}")
                sys.exit(1)
                
            print(f"Running tests from {os.path.basename(test_path)}:")
            result = runner.run(suite)
            sys.exit(0 if result.wasSuccessful() else 1)
        except Exception as e:
            print(f"Error loading tests from {test_path}: {e}")
            sys.exit(1)
    else:
        # Run tests from directory
        if os.path.isdir(test_path):
            # Check if specific test method is requested (not allowed for directories)
            if args.method:
                print(f"Error: Cannot specify a specific test method when running tests from a directory")
                print(f"Please specify a specific test file with: {sys.argv[0]} path/to/test_file.py -m test_method")
                sys.exit(1)
                
            print(f"Running all tests in {test_path}")
            suite = collect_tests(test_path)
            
            if not suite.countTestCases():
                print(f"No tests found in {test_path}")
                sys.exit(1)
                
            result = runner.run(suite)
            sys.exit(0 if result.wasSuccessful() else 1)
        else:
            print(f"Error: Test path {test_path} does not exist or is not a Python file")
            sys.exit(1)

if __name__ == '__main__':
    main()
