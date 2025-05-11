# Jibberish Testing Guide

The Jibberish shell includes a comprehensive test suite using Python's unittest framework. These tests ensure that all components of the shell work as expected.

## Running the Test Suite

The simplest way to run all tests is using the provided test runner script:

```bash
cd /home/brownjer/bin/jibberish
python3 tests/run_tests.py
```

This will automatically find and run all tests in the project.

## Running Specific Tests

You can run tests from a specific directory:

```bash
# Run only plugin tests
python3 tests/run_tests.py tests/plugins

# Run only framework tests
python3 tests/run_tests.py tests/framework
```

Or run a specific test file:

```bash
# Run tests for the alias command
python3 tests/run_tests.py tests/plugins/test_alias_command.py

# Run tests for the executor module
python3 tests/run_tests.py tests/framework/test_executor.py
```

## Running Individual Test Methods

You can run a specific test method within a file using the `-m` flag:

```bash
# Run a specific test method
python3 tests/run_tests.py tests/plugins/test_cd_command.py -m test_execute_home_directory

# Run a test method with the class name specified
python3 tests/run_tests.py tests/plugins/test_cd_command.py -m TestCDCommand.test_execute_home_directory
```

## Additional Options

The test runner script supports these additional options:

- `-v` or `--verbose`: Increase output verbosity for more detailed test information
- `-m METHOD` or `--method METHOD`: Specify a test method to run

## Using Standard Unittest

You can also run the tests using Python's standard unittest module:

```bash
# Run all tests
python3 -m unittest discover -s tests

# Run tests in a specific file
python3 -m unittest tests/plugins/test_cd_command.py
```

## Using Jibberish to Run Tests

Of course... you could just ask Jibberish to do it 😃
```bash
/home/brownjer/bin/jibberish#  #run all the python tests under the tests directory
pytest tests/
Execute this command? [y/n]: y
Executing: pytest tests/
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-8.3.5, pluggy-1.5.0
rootdir: /home/brownjer/bin/jibberish
plugins: cov-4.1.0, anyio-4.8.0
collected 113 items

tests/framework/test_chat_history.py ....                                [  3%]
tests/framework/test_context_manager.py ..                               [  5%]
tests/framework/test_executor.py .............                           [ 16%]
tests/framework/test_history.py ...........                              [ 26%]
tests/framework/test_history_limit.py .....                              [ 30%]
tests/plugins/test_ai_command.py .....                                   [ 35%]
tests/plugins/test_alias_command.py ...........                          [ 45%]
tests/plugins/test_alias_expansion.py ....                               [ 48%]
tests/plugins/test_cd_command.py ......                                  [ 53%]
tests/plugins/test_change_partner_command.py ...                         [ 56%]
tests/plugins/test_dir_stack_command.py ..........                       [ 65%]
tests/plugins/test_export_command.py ......                              [ 70%]
tests/plugins/test_history_command.py ....                               [ 74%]
tests/plugins/test_history_retrieval_command.py .....                    [ 78%]
tests/plugins/test_job_control_command.py ▶ Background job [1]: tail -f file1.txt
  Output stream will update automatically... (PID: 12345)

.============================================================
[1] Completed: tail -f file1.txt
Job output:
$ tail -f file1.txt
(No output)
Press the <ENTER> key
.........                     [ 87%]
tests/plugins/test_question_command.py ....                              [ 91%]
tests/plugins/test_ssh_command.py .....                                  [ 95%]
tests/plugins/test_version_command.py ...                                [ 98%]
tests/test_context_manager.py ..                                         [100%]

============================= 113 passed in 2.60s ==============================
```
