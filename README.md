# Jibberish
## Linux AI Shell

### Commands:
- `<command>`                 - Execute a shell command
- `#<command>`                - Ask the AI to generate shell commands based on the user input
- `?<question>`               - Ask a general question
- `exit`, `quit`, `q`         - Exit the shell          
- `help`                      - Help menu

### ~/.jbrsh
- Add this file to your home directory
- This file contains environment variables used within the shell
- You will need to fill out ENV variables to connect to your AI service

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

