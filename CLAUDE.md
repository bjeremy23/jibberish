# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Jibberish is an AI-powered Linux shell (Python 3.8+) that translates natural language into shell commands using OpenAI/Azure OpenAI APIs. Users interact via three input modes:
- `#<description>` — lightweight command generation (fewer tokens, no tools)
- `?<question>` — conversational AI with tool support (file read/write, MCP, linux commands)
- `<command>` — direct shell execution with alias expansion, error correction, and output recall

## Build & Run

```bash
# Setup (creates venv, installs deps, creates ~/.jbrsh config)
./setup.sh

# Run interactively
source venv/bin/activate
python app/jibberish.py

# Standalone mode
python app/jibberish.py -v              # version
python app/jibberish.py -q "question"   # ask question
python app/jibberish.py -c "description" # generate & execute command
```

## Testing

Tests use Python's `unittest` framework via a custom runner (`tests/run_tests.py`). No pytest.

```bash
# Run all tests
python tests/run_tests.py

# Run tests in a specific directory
python tests/run_tests.py tests/plugins/

# Run a specific test file
python tests/run_tests.py tests/plugins/test_alias_expansion.py

# Run a specific test method
python tests/run_tests.py tests/plugins/test_alias_expansion.py -m test_method_name

# Run with class.method format
python tests/run_tests.py tests/plugins/test_explain_command.py -m ExplainCommandTests.test_can_handle

# Verbose output
python tests/run_tests.py -v
```

## Architecture

### Request Flow

1. **`app/jibberish.py`** — Entry point and main REPL loop. Reads user input and delegates via `execute_command_with_built_ins()` from utils.
2. **`app/built_ins.py`** — First check: queries the plugin registry (`BuiltinCommandRegistry.find_handler()`) to see if a plugin handles the input. Plugins are loaded dynamically at import time.
3. **`app/executor.py`** — If no plugin handles it, executes as a shell command. Handles alias expansion (including parameterized aliases with `{1}`, `{*}`), command chaining (`&&`, `;`), background processes (`&`), and interactive vs non-interactive detection.
4. **`app/chat.py`** — AI interaction layer. `ask_ai()` generates commands from `#` input. `ask_question()` handles `?` input with a multi-iteration tool execution loop (up to 6 rounds of tool calls).
5. **`app/api.py`** — Initializes the OpenAI/Azure client at import time by reading `~/.jbrsh` config file. Exposes `api.client` and `api.model` globally.

### Plugin System

Plugins extend the shell with built-in commands. Each plugin in `app/plugins/` subclasses `BuiltinCommand` (from `app/plugin_system.py`) and self-registers with `BuiltinCommandRegistry`.

A plugin must implement:
- `can_handle(command)` — returns `True` if this plugin should process the command
- `execute(command)` — runs the command; returns `True` (handled), `False` (not handled), or `(False, new_command)` to pass a transformed command back

Plugins are either `is_required=True` (always loaded) or optional (controlled by `PLUGIN_<NAME>_ENABLED` env var). Plugins are auto-discovered from the `app/plugins/` directory via `pkgutil.iter_modules`.

### Tool System

Tools in `app/tools/` let the AI perform actions during `?` queries. Each tool subclasses `Tool` (from `app/tools/base.py`) and registers with `ToolRegistry`.

A tool must implement: `name`, `description`, `parameters` (JSON schema), and `execute(**kwargs)`.

Built-in tools: `file_reader`, `file_writer`, `linux_command`. MCP server tools are dynamically registered at startup from config.

The AI invokes tools by including JSON in its response:
```json
{"tool_calls": [{"name": "tool_name", "arguments": {"param": "value"}}]}
```
`ToolCallParser` extracts these from the AI response text (not via OpenAI function calling API).

### Key Modules

- **`app/context_manager.py`** — Adds domain-specific system prompts (SSH, git, docker, k8s, etc.) based on keyword detection in user input. Also determines temperature per query type.
- **`app/output_history.py`** — Stores recent command outputs for recall via `$_`, `@0`, `@1`, etc. Injected into AI context when references are detected.
- **`app/utils.py`** — Shared utilities: debug flag (`JIBBERISH_DEBUG`), chat history persistence, tool context message generation, prompt-before-execution logic (`PROMPT_AI_COMMANDS`).

## Configuration

All config lives in `~/.jbrsh` (key=value format, loaded by `app/api.py` at import). Key settings:
- `AI_CHOICE` — `openai` or `azure`
- `OPEN_API_KEY` / `OPEN_API_MODEL` — for standard OpenAI
- `AZURE_*` vars — for Azure OpenAI (supports managed identity, CLI credential, or API key auth)
- `JIBBERISH_DEBUG` — enables verbose output
- `PROMPT_AI_COMMANDS` — require confirmation before executing AI-generated commands
- `WARN_LIST` — comma-separated commands that trigger confirmation prompts
- `IGNORE_ERRORS` — suppress error explanation prompts
- `JIBBERISH_PROMPT` — custom prompt format with `%u`, `%h`, `%p` placeholders
