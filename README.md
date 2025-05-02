# Jibberish
## Linux AI Shell

### Commands:
- `<command>`                 - Execute a shell command
- `#<command description>`    - Ask the AI to generate shell commands based on the user input
- `##<command description>`   - Ask the AI to generate commented shell commands based on the user input
- `?<question>`               - Ask a general question
- `exit`, `quit`, `q`         - Exit the shell          
- `help`                      - Help menu

### Standalone Mode

Jibberish can also be used in standalone mode (non-interactive) by passing command-line options. This is useful for scripts or when you want to execute a single command without starting the full interactive shell.

#### Available Options:

- `-v, --version`: Display version information
- `-q, --question "your question"`: Ask a general question (without needing the '?' prefix)
- `-c, --command "command description"`: Generate and execute a command (without needing the '#' prefix)
- `-h, --help`: Display help information

#### Examples:

```bash
# Show version information
python jibberish.py -v

# Ask a question
python jibberish.py -q "What is Linux?"

# Generate and execute a command
python jibberish.py -c "find all text files modified in the last week"

# Show help
python jibberish.py -h
```

The standalone mode is designed to be clean and concise, outputting only the relevant information without any debug or environment loading messages.

### ~/.jbrsh
- Add this file to your home directory
- This file contains environment variables used within the shell
- You will need to fill out ENV variables to connect to your AI service

For detailed instructions on setting up your API credentials, see [README-setup.md](README-setup.md).

### Plugins
The Jibberish shell includes several plugins that extend its functionality:

- **ai_command.py** - Processes commands starting with `#` and uses AI to generate shell commands based on natural language descriptions
  - Usage: `#find large files in my home directory`
  - Example:
    ```
    /home/user# #find files larger than 100MB in the current directory
    find . -type f -size +100M -exec ls -lh {} \; | sort -k5,5nr
    
    Executing: find . -type f -size +100M -exec ls -lh {} \; | sort -k5,5nr
    -rw-r--r-- 1 user group 235M Apr 19 10:23 ./large_dataset.zip
    -rw-r--r-- 1 user group 125M Apr 18 15:45 ./logs/system.log
    ```
  - You can also use `##` to generate commands without executing them (useful for learning or reviewing commands first)
  - Example:
    ```
    /home/user# ##monitor system load for 10 seconds
    # vmstat 1 10
    
    /home/user# ##find all Docker containers including stopped ones
    # docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}"
    ```

- **alias_command.py** - Manages command aliases that persist between shell sessions
  - Usage: `alias ls='ls -FC'` to create an alias
  - Example:
    ```
    /home/user# alias ls='ls -FC'
    Alias set: ls -> ls -FC
    
    /home/user# alias
    Current aliases:
    alias ls='ls -FC'
    
    /home/user# ls
    bin/   Documents/   Downloads/   projects/   
    ```
  - Use `alias` to list all aliases
  - Use `unalias ls` to remove an alias

- **cd_command.py** - Enhanced directory navigation
  - Usage: `cd path/to/directory`
  - Example:
    ```
    /home/user# cd /var/log
    /var/log# cd ~
    /home/user#
    ```
  - Supports home directory with `cd ~` 
  - Handles errors gracefully with clear messages

- **change_partner_command.py** - Allows switching Your AI companion
  - Usage: `:) Batman`
  - Example:
    ```
    /home/user# :) Batman
    Now talking with  Batman

    /home/user# ? What do you think is the biggest problem today?
    There are a lot of problems in this world—corruption, greed, fear. But if I had to pick one, I’d say **apathy**. Too many people see injustice and look the other way. They think someone else will handle it. Evil thrives when good people do nothing.

    That’s why I do what I do. Because sometimes, all it takes is one person willing to act. 
    ```

- **dir_stack_command.py** - Implements directory stack operations (similar to pushd/popd in bash)
  - Usage: `pushd`, `popd`, `dirs` commands for directory stack manipulation
  - Example:
    ```
    /home/user# pushd /etc
    /etc ~
    /etc# pushd /var/log
    /var/log /etc ~
    /var/log# popd
    /etc ~
    /etc# dirs
    /etc ~
    ```

- **export_command.py** - Sets environment variables within the shell session
  - Usage: `export VAR=value`
  - Example:
    ```
    /home/user# export DEBUG=true
    Environment variable set: DEBUG=true
    
    /home/user# echo $DEBUG
    true
    ```

- **history_command.py** - Manages and displays command history
  - Usage: `history` to show command history
  - Example:
    ```
    /home/user# history
    1  ls -la
    2  cd Documents
    3  cat file.txt
    4  #find large files
    5  history
    ```

- **history_retrieval_command.py** - Retrieves and re-executes commands from history
  - Usage: `!<number>` or `!<string>` to recall and execute commands from history
  - Example:
    ```
    /home/user# !3
    Executing: cat file.txt
    This is the content of the file.
    
    /home/user# !cd
    Executing: cd Documents
    /home/user/Documents#
    ```
    
- **job_control_command.py** - Provides background process management similar to bash's job control
  - Usage: Commands ending with `&` run in background, `jobs` lists jobs, `fg` brings jobs to foreground
  - Example:
    ```
    /home/user# tail -f logfile.txt &
    [1] Running in background: tail -f logfile.txt (PID: 12345)
    
    /home/user# jobs
    Updating job status...
    Job 1 (PID 12345): tail -f logfile.txt - Status: sleeping
    Jobs:
    [1] Running (PID: 12345) tail -f logfile.txt
    
    /home/user# fg
    ### Processing Jibberish fg command ###
    Updating job status...
    Job 1 (PID 12345): tail -f logfile.txt - Status: sleeping
    Bringing job 1 (tail -f logfile.txt) to foreground
    Process is sleeping
    Note: Full job control is limited in Jibberish shell. Here are your options:
    1. Process ID: 12345 - You can use 'kill -15 12345' to terminate if needed
    Do you want to see the content of logfile.txt now? (y/n): y
    
    --- Content of logfile.txt ---
    [log content appears here]
    ^C
    
    Restart 'tail -f logfile.txt' in the background? (y/n): y
    Restarting in background: tail -f logfile.txt
    [2] Running in background: tail -f logfile.txt (PID: 12346)
    ```
  - Use `fg %2` to bring a specific job to the foreground
  - Configure which apps run interactively via `INTERACTIVE_LIST` in `.jbrsh`

- **question_command.py** - Processes questions starting with `?` and provides AI-generated answers
  - Usage: `?what is a shell script?`
  - Example:
    ```
    /home/user# ?what is a shell script?
    A shell script is a text file containing a sequence of commands that are executed by a shell program. 
    It allows users to automate tasks in Unix/Linux environments by combining multiple commands together.
    
    Shell scripts typically have a .sh extension and start with a "shebang" line like #!/bin/bash that 
    specifies which shell interpreter should be used. They're used for system administration tasks, 
    application startup procedures, and automating repetitive tasks.
    ```

- **ssh_command.py** - Enhances SSH connections with additional features
  - Usage: `ssh user@hostname [command]`
  - Example:
    ```
    /home/user# ssh server1 "df -h"
    Connected to server1...
    Filesystem      Size  Used Avail Use% Mounted on
    /dev/sda1        50G   15G   35G  30% /
    /dev/sdb1       500G  100G  400G  20% /data
    ```
    
### Running Tests

The Jibberish shell includes a comprehensive test suite using Python's unittest framework. These tests ensure that all components of the shell work as expected.

#### Running the Test Suite

The simplest way to run all tests is using the provided test runner script:

```bash
cd /home/brownjer/bin/jibberish

```python3 tests/run_tests.py

This will automatically find and run all tests in the project.

#### Running Specific Tests

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

#### Running Individual Test Methods

You can run a specific test method within a file using the `-m` flag:

```bash
# Run a specific test method
python3 tests/run_tests.py tests/plugins/test_cd_command.py -m test_execute_home_directory

# Run a test method with the class name specified
python3 tests/run_tests.py tests/plugins/test_cd_command.py -m TestCDCommand.test_execute_home_directory
```

#### Additional Options

The test runner script supports these additional options:

- `-v` or `--verbose`: Increase output verbosity for more detailed test information
- `-m METHOD` or `--method METHOD`: Specify a test method to run

#### Using Standard Unittest

You can also run the tests using Python's standard unittest module:

```bash
# Run all tests
python3 -m unittest discover -s tests

# Run tests in a specific file
python3 -m unittest tests/plugins/test_cd_command.py
```

#### Of course... you could just ask Jibberish to do it
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
