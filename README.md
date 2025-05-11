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
The Jibberish shell includes several plugins that extend its functionality. 

For a complete list of available plugins and detailed documentation on how to use them, see [README-plugins.md](README-plugins.md).

This documentation covers:
- Available plugins and their usage examples
- Required vs optional plugins
- How to enable or disable optional plugins
- Creating your own plugins
 
### Testing

The Jibberish shell includes a comprehensive test suite to ensure all components work as expected.

For detailed instructions on running tests, see [README-tests.md](README-tests.md).
```
