# Jibberish Shell Plugins

The Jibberish shell includes several plugins that extend its functionality. This document describes the available plugins and how to configure them.

## Available Plugins

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
    There are a lot of problems in this world—corruption, greed, fear. But if I had to pick one, I'd say **apathy**. Too many people see injustice and look the other way. They think someone else will handle it. Evil thrives when good people do nothing.

    That's why I do what I do. Because sometimes, all it takes is one person willing to act. 
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

## Plugin System: Required vs Optional Plugins

The Jibberish shell has a flexible plugin system that categorizes plugins as either **required** or **optional**:

- **Required Plugins**: Always loaded and cannot be disabled. These provide core functionality for the shell.
- **Optional Plugins**: Can be enabled or disabled via environment variables in your `.jbrsh` file.

### Enabling/Disabling Optional Plugins

To control which optional plugins are loaded, you can set environment variables in your `.jbrsh` file:

```bash
# Enable the version command plugin
PLUGIN_OPTIONAL_COMMAND_ENABLED=y

# Disable the ssh command plugin
PLUGIN_OPTINAL_COMMAND_ENABLED=n
```

Valid values for enabling a plugin: `y`, `yes`, `true`, `1`  
Valid values for disabling a plugin: `n`, `no`, `false`, `0` (or any other value)

### Creating New Optional Plugins

When developing your own plugins for Jibberish, follow these steps to make them optional:

1. Extend the `BuiltinCommand` class and set the plugin attributes:
   ```python
   class MyCustomPlugin(BuiltinCommand):
       # Plugin attributes
       plugin_name = "my_custom_plugin"  # Name of the plugin (used in env var names)
       is_required = False               # Set to False for optional plugins
       is_enabled = True                 # Default state (can be overridden by env var)
   ```

2. The plugin system automatically checks for an environment variable with the naming pattern:
   ```
   PLUGIN_<PLUGIN_NAME>_ENABLED
   ```
   where `<PLUGIN_NAME>` is the uppercase version of your `plugin_name` attribute.

3. Register your plugin with the registry:
   ```python
   # Register the plugin with the registry
   BuiltinCommandRegistry.register(MyCustomPlugin())
   ```

The plugin will only be loaded if either:
- It's marked as required (`is_required = True`)
- It's optional but enabled via environment variable or default setting (`is_enabled = True`)
