# Jibberish
## Linux AI Shell

## TL;DR

Jibberish is an AI-powered Linux shell that revolutionizes command-line interaction with three key features:

1. **Natural Language CLI** - Forget complex syntax. Describe what you want in plain English and get executable commands instantly. Use `?` to invoke the chat for queries that leverage MCP servers or built-in tools like file read/write. Use `#` as a lightweight shortcut to generate specific Linux commands without incurring extra token usage.

2. **MCP Server Integration** - Seamlessly integrate Model Context Protocol (MCP) servers to extend AI capabilities. Connect to Docker containers, local processes, or HTTP endpoints to add specialized tools like Kubernetes management, code analysis, custom made tools, and more.

3. **Plugin Framework** - Extend the cli functionality with a powerful plugin system. Built-in plugins handle SSH, history, job control, and more. Create custom plugins to add domain-specific commands and behaviors to your shell.

---

For installation instructions, see [README-installation.md](README/README-installation.md).

### Commands:
- `<command>`                 - Execute a shell command
- `#<command description>`    - Ask to generate a command - less tokens, exact and concise
- `?<question>`               - Ask a question or perform tasks using tools - more tokens, more verbiage and detail
- `exit`, `quit`, `q`         - Exit the shell          
- `help`                      - Help menu

### Examples

The following examples demonstrate some of Jibberish's capabilities:

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
ssh $MASTER "kubectl -n fed-test get pods | grep vpp | awk '{print \$1}' | xargs -I{} kubectl -n fed-test exec {} -- vppctl show thread usage"
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

### File Tools

Jibberish includes built-in tools for reading and writing files, which can be used through natural language commands when asking questions with the `?` prefix:

#### Reading Files

Ask Jibberish to read and analyze file contents:

```bash
# Read a specific file
/home/jbrsh# ? Using the ./README, summarize the key features

# Read parts of a file
/home/jbrsh# ? Read the first 20 lines of /var/log/syslog and tell me about any errors

# Analyze configuration files
/home/jbrsh# ? Check my ~/.bashrc file and explain what customizations I have
```

#### Writing Files

Ask Jibberish to create or update files based on your requests:

```bash
# Create a summary file
/home/jbrsh# ? Read the documentation and create a quick reference guide in /tmp/quick-ref.md

# Generate configuration files
/home/jbrsh# ? Create a basic nginx.conf file for a static website in /tmp/nginx.conf

# Save command output to files
/home/jbrsh# ? Analyze the system logs and write a summary to /tmp/log-analysis.txt
```

#### Combined File Operations

You can combine reading and writing operations in a single request:

```bash
# Process and transform files
/home/jbrsh# ? Read the CSV data from ./input.csv, format it as markdown table, and save to ./output.md

# Create reports from multiple sources
/home/jbrsh# ? Using both ./config.yaml and ./logs.txt, create a system status report in /tmp/status.md
```

The file tools support:
- **Any file path**: Absolute paths, relative paths, or tilde (`~`) for home directory
- **Multiple encodings**: UTF-8 (default), ASCII, Latin-1
- **Append mode**: Add content to existing files instead of overwriting
- **Automatic directory creation**: Creates parent directories if they don't exist
- **Error handling**: Clear error messages for permission issues or invalid paths

These tools integrate seamlessly with Jibberish's AI capabilities, allowing you to work with files using natural language rather than remembering complex command syntax.

### MCP Server Integration

Jibberish supports the Model Context Protocol (MCP), allowing you to connect to multiple MCP servers that provide additional tools and capabilities. MCP servers can run locally as Docker containers, executables, or remote HTTP endpoints.

For complete setup instructions, configuration options, server types, and detailed usage examples, see [README/README-mcp-servers.md](README/README-mcp-servers.md).

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

### Configuration

For detailed instructions on setting up your API credentials and configuring Jibberish, see [README/README-ai-setup.md](README/README-ai-setup.md).

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

### Debug Mode

Jibberish runs in a clean mode by default, showing only the essential output for commands. If you want to see detailed output including:

- Environment variable loading
- Plugin registration messages
- API initialization details

You can enable debug mode in one of two ways:

1. **Temporarily** - For a single command:
   ```bash
   JIBBERISH_DEBUG=true jibberish -v
   ```

2. **Permanently** - Add to your ~/.jbrsh file:
   ```
   JIBBERISH_DEBUG=true
   ```

When debug mode is disabled (the default), you'll get clean output like this:

```bash
$ jibberish -v
Jibberish v25.5.4
Javanese
```

When debug mode is enabled, you'll see all diagnostic information:

```bash
$ JIBBERISH_DEBUG=true jibberish -v
Set AI_CHOICE to azure
Set AZURE_CLIENT_ID to 0272f95e-051c-4d0f-8950-9b9de3f08ea0
...
Loading plugins...
Registered plugin: ai_command - required
...
Jibberish v25.5.4
Javanese
```
