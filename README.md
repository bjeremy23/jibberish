# Jibberish
## Linux AI Shell

### Commands:
- `<command>`                 - Execute a shell command
- `#<command description>`    - Ask the AI to generate shell commands based on the user input
- `?<question>`               - Ask a general question
- `exit`, `quit`, `q`         - Exit the shell          
- `help`                      - Help menu

### Examples

The following examples demonstrate some of Jibberish's powerful capabilities:

#### Natural Language Command Generation

Instead of remembering complex syntax, describe what you want to do:

```bash
# Find large log files using natural language
/home/jbrsh# #find log files larger than 100MB and sort by size

# Jibberish generates:
find /var/log -type f -size +100M -exec ls -lh {} \; | sort -k5,5hr
```

#### Complex Commands with Environment Variables

Jibberish can leverage environment variables defined in your `~/.jbrsh` file to streamline complex commands:

```bash
# SSH to $MASTER and find the VPP pod in fed-test namespace to show thread usage
/home/jbrsh# ssh $MASTER "kubectl -n fed-test get pods | grep vpp | awk '{print \$1}' | xargs -I{} kubectl -n fed-test exec {} -- vppctl show thread usage"
```

This single command:
1. Connects to the server defined in your `$MASTER` environment variable 
2. Finds the VPP pod in the fed-test namespace
3. Executes the 'vppctl show thread usage' command within that pod

#### Get Answers in your workflow

Jibberish lets you ask questions directly within your working context using the `?` prefix, without disrupting your workflow:

``` bash
/home/jbrsh# ? find the latest version of trivy

You can always check the most current release on their [GitHub releases page](https://github.com/aquasecurity/trivy/releases), because, of course, nothing ever stays the same for long.
```

This feature allows you to:
- Get immediate answers without leaving the command line
- Maintain your working directory context
- Access up-to-date information on tools, packages, and technologies
- Receive responses that include both facts and markdown formatting for better readability

#### Command Correction

If you make a typo or error in your command, Jibberish will intelligently suggest corrections:

```bash
# Typing a command with an error
/home/jbrsh# la -la

# Jibberish suggests:
la: command not found
Did you mean 'ls -la'? Run this command instead? [y/n]: y

```

#### Command Chaining with AI Assistance

You can mix regular commands with AI-assisted commands:

```bash
# Chain commands with && or ;
/home/jbrsh# #show system memory usage && df -h

# Jibberish executes:
free -h && df -h

```

#### Error Handling and Explanation

When commands produce errors, If the option is enabled in the .jbrsh env file, Jibberish provides helpful feedback and offers explanations:

```bash
# Using curl with incorrect proxy syntax
/home/jbrsh# curl -x GET www.yahoo.com

# Jibberish shows the error:
curl: (5) Could not resolve proxy: GET

# Jibberish offers additional help:
More information about the error? [y/n]: y

The error occurs because the -x flag in curl expects a proxy URL, not an HTTP method.
To use HTTP GET method with curl, simply use:
curl www.yahoo.com

Or to explicitly specify the GET method:
curl -X GET www.yahoo.com
```

#### Interactive and Background Processes

Jibberish handles both interactive commands and background processes:

```bash
# Background process
/home/jbrsh# nohup python -m http.server 8080 &

# Interactive command
/home/jbrsh# top
```

For more advanced usage and detailed documentation on specific features, refer to the guides linked below.

### Installation

Jibberish provides a simple setup script to install all dependencies and configure your environment. This script will:

1. Create a Python virtual environment
2. Install all required dependencies
3. Configure the `.jbrsh` configuration file in your home directory
4. Verify the installation

#### Standard Installation

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/bjeremy23/jibberish.git
cd jibberish

# Run the setup script
./setup.sh
```

#### Installation Options

The setup script supports several command-line options:

```bash
Usage: ./setup.sh [options]
Options:
  --non-interactive    Run without prompts (assumes yes for all questions)
  --with-azure         Install Azure OpenAI dependencies
  --yes, -y            Answer yes to all prompts
  --help, -h           Show this help message
```

#### Examples

```bash
# Install with Azure OpenAI support
./setup.sh --with-azure

# Non-interactive installation for CI/CD environments
./setup.sh --non-interactive

# Automatically answer yes to all prompts
./setup.sh --yes
```

After installation, you'll need to edit the `~/.jbrsh` file to add your API keys and customize settings. For detailed instructions on setting up your API credentials, see [README/README-setup.md](README/README-setup.md).

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

For detailed instructions on setting up your API credentials, see [README/README-setup.md](README/README-setup.md).

### Plugins
The Jibberish shell includes several plugins that extend its functionality. 

For a complete list of available plugins and detailed documentation on how to use them, see [README/README-plugins.md](README/README-plugins.md).

This documentation covers:
- Available plugins and their usage examples
- Required vs optional plugins
- How to enable or disable optional plugins
- Creating your own plugins


### Testing

The Jibberish shell includes a comprehensive test suite to ensure all components work as expected.

For detailed instructions on running tests, see [README/README-tests.md](README/README-tests.md).
