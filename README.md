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

#### Setting up Azure OpenAI Credentials

To use the Jibberish shell with Azure OpenAI, you'll need to set up the following credentials in your `~/.jbrsh` file:

1. **AZURE_OPENAI_API_KEY** - Your Azure OpenAI API key
2. **AZURE_OPENAI_ENDPOINT** - Your Azure OpenAI service endpoint URL
3. **AZURE_OPENAI_API_VERSION** - The Azure OpenAI API version to use (e.g., "2023-05-15")
4. **AZURE_OPENAI_DEPLOYMENT_NAME** - The name of your deployed model (e.g., "gpt-4.1")

##### How to obtain Azure OpenAI credentials:

1. **Create an Azure account**: If you don't have an Azure account yet, sign up at [https://azure.microsoft.com](https://azure.microsoft.com).

2. **Request access to Azure OpenAI**: Azure OpenAI is currently available by application only. Apply for access at [https://aka.ms/oai/access](https://aka.ms/oai/access).

3. **Create an Azure OpenAI resource**:
   - Log in to the [Azure Portal](https://portal.azure.com)
   - Search for "Azure OpenAI" and select it
   - Click "Create"
   - Fill in the required details (resource name, subscription, resource group, region)
   - Click "Review + create", then "Create"

4. **Deploy a model**:
   - Go to your newly created Azure OpenAI resource
   - Select "Model deployments" from the left menu
   - Click "Create new deployment"
   - Select a model (e.g., "gpt-4", "gpt-4.1")
   - Set a deployment name (you'll use this as AZURE_OPENAI_DEPLOYMENT_NAME)
   - Configure other settings as needed
   - Click "Create"

5. **Get your credentials**:
   - From your Azure OpenAI resource page, go to "Keys and Endpoint"
   - Copy one of the keys (either KEY1 or KEY2) for AZURE_OPENAI_API_KEY
   - Copy the Endpoint URL for AZURE_OPENAI_ENDPOINT
   - For AZURE_OPENAI_API_VERSION, use the latest stable version (e.g., "2023-05-15")

6. **Add credentials to ~/.jbrsh**:
   ```
   AZURE_OPENAI_API_KEY="your-api-key-here"
   AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com/"
   AZURE_OPENAI_API_VERSION="2023-05-15"
   AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment-name"
   ```

**Note**: Keep your API key secure and never share it publicly.

#### Using Entra ID authentication instead of key-based authentication
Alternatively, to avoid the use of an API key, Jibberish supports authentication via Azure AD (Entra ID) methods and RBAC role assignment.  Both Managed Identity and Azure CLI interactive login are supported.

##### Managed Identity of System-Assigned Identity
When running Jibberish in an Azure virtual machine, it is recommended to use the system-assigned identity or user-assigned managed identity of the VM resource to authenticate usage of Azure OpenAI.  The steps to utilize a managed identity are:

1. Ensure your Managed Identity in Azure is assigned RBAC roles on the Azure OpenAI resource.
   - Assign the Managed Identity/System Identity the "Cognitive Services OpenAI User" role on the Open AI instance
     
2. Configure the ~/.jbrsh file
   - Remove/comment the variable ```AZURE_OPENAI_API_KEY```
   - Add the variable ```AZURE_CLIENT_ID``` with the value of the client_id of the managed identity
   ```
   #AZURE_OPENAI_API_KEY="your-api-key-here"
   AZURE_CLIENT_ID="your-managed-identity-client-id-here"
   ```

##### Azure CLI interactive login
Jibberish supports interactive Azure CLI login for authentication.

1. Ensure your user ID is assigned RBAC roles on the Azure OpenAI resource.
   - Assign your user identity the "Cognitive Services OpenAI User" role on the Open AI instance
     
2. Configure the ~/.jbrsh file
   - Remove/comment the variable ```AZURE_OPENAI_API_KEY```
   - Add the variable ```AZURE_USER_NAME``` with the value of the user name you are using for login
   ```
   #AZURE_OPENAI_API_KEY="your-api-key-here"
   AZURE_USER_NAME="your-username@domein.com"
   ```

#### Setting up OpenAI Credentials

As an alternative to Azure OpenAI, you can directly use OpenAI's services. You'll need to set up the following credentials in your `~/.jbrsh` file:

1. **OPEN_API_KEY** - Your OpenAI API key
2. **OPEN_API_MODEL** - The OpenAI model to use (e.g., "gpt-4", "gpt-4-turbo", "gpt-4o")

##### How to obtain OpenAI credentials:

1. **Create an OpenAI account**: Sign up at [https://platform.openai.com/signup](https://platform.openai.com/signup).

2. **Get your API key**:
   - Log in to your OpenAI account at [https://platform.openai.com](https://platform.openai.com)
   - Click on your profile icon in the top-right corner
   - Select "View API keys"
   - Click "Create new secret key"
   - Give your key a name (optional) and click "Create"
   - Copy your API key (you won't be able to see it again)

3. **Choose a model**:
   - OpenAI offers various models with different capabilities and pricing
   - Common choices include:
     - `gpt-4` - Most powerful reasoning and instruction following
     - `gpt-4-turbo` - Faster version of GPT-4 with updated knowledge
     - `gpt-4o` - The latest GPT-4 model with improved performance
     - `gpt-3.5-turbo` - Faster and more cost-effective for simpler tasks

4. **Add credentials to ~/.jbrsh**:
   ```
   OPEN_API_KEY="your-openai-api-key-here"
   OPEN_API_MODEL="gpt-4"
   ```

5. **Set up billing**:
   - Go to [https://platform.openai.com/account/billing/overview](https://platform.openai.com/account/billing/overview)
   - Add a payment method
   - Set up usage limits to control costs (recommended)

**Note**: OpenAI API usage incurs costs based on your usage. Monitor your usage to avoid unexpected charges.

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

