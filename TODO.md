# Jibberish Feature TODO

Feature suggestions to improve the CLI user experience.

---

## 1. Command Output Recall with `$_` or `@n` Syntax ⭐ High Impact - [x] COMPLETED

Allow users to reference output from previous commands without re-running them:

```bash
/home/user# ls *.log
error.log  access.log  debug.log

/home/user# #compress all the files from the last output
tar -czvf logs.tar.gz error.log access.log debug.log  # AI uses $_ context
```

**Status: IMPLEMENTED**

The feature is now available. Command outputs are automatically stored and can be referenced:
- Use `$_` or `@0` to reference the most recent output
- Use `@1`, `@2`, etc. for older outputs
- Natural language like "that", "those", "the output" also triggers context injection

**Implementation Details:**
- Created `app/output_history.py` module for storing/retrieving outputs
- Modified `app/executor.py` to capture outputs after command execution  
- Modified `app/chat.py` to inject output context into AI prompts
- Added comprehensive tests in `tests/framework/test_output_history.py`

---

## 2. Parameterized Aliases with Placeholders — Medium Impact

Extend the alias system to support parameter substitution:

```bash
/home/user# alias port='lsof -i :{1}'
/home/user# port 8080   # expands to: lsof -i :8080

/home/user# alias klog='kubectl logs -n {1} {2} --tail=100'
/home/user# klog production my-pod
```

**Benefits:**
- Reduces repetitive typing for commands that only differ by one or two arguments
- More powerful than simple text substitution aliases
- Familiar pattern for users coming from shell functions

**Implementation Notes:**
- Parse `{1}`, `{2}`, etc. placeholders in alias definitions
- Support optional default values: `{1:-default}`
- Update `alias_command.py` to handle expansion

---

## 3. Consolidate `history` and `!` Commands — Simplification

Currently there are two separate plugins:
- `history_command.py` - shows history
- `history_retrieval_command.py` - re-executes with `!n` or `!string`

Unify into a single `history` plugin with subcommands:

```bash
history           # list recent commands
history search    # interactive fuzzy search
history 5         # execute command #5 (replaces !5)
history grep ssh  # filter history (replaces !ssh behavior)
```

**Benefits:**
- Reduces cognitive load by having one command namespace
- More discoverable for new users
- Consistent interface

**Implementation Notes:**
- Merge plugins or have one delegate to the other
- Keep `!n` syntax as backward-compatible shortcut
- Add fuzzy search capability

---

## 4. Smart Command Suggestions on Empty Enter — Low Friction

When the user presses Enter on an empty prompt, show contextual suggestions:

```bash
/var/log# <enter>
Suggestions based on directory:
  1. tail -f syslog
  2. ls -lt | head
  3. grep -r "error" .
```

**Benefits:**
- Helps users discover relevant commands
- Context-aware suggestions based on directory and history
- Reduces "what was that command again?" friction

**Implementation Notes:**
- Analyze current directory (e.g., `/var/log` → log-related commands)
- Consider recent command history patterns
- Keep it lightweight (local heuristics vs. AI call)
- Make it optional/configurable

---

## 5. `explain` Command for Learning — Educational

A lightweight command to explain any Linux command without executing:

```bash
/home/user# explain tar -xzvf archive.tar.gz
  tar       - Archive utility
  -x        - Extract files
  -z        - Filter through gzip
  -v        - Verbose output
  -f        - Use archive file
```

**Benefits:**
- Lower token cost than `?` since it doesn't need MCP/tools
- Helps users learn command syntax
- Quick reference without leaving the shell

**Implementation Notes:**
- Create as new plugin `explain_command.py`
- Use focused system prompt for command explanation
- Could parse man pages locally as fallback
- Consider caching common explanations

---

## Priority Recommendation

Start with **#1 (Output Recall)** — it's the most impactful for workflow efficiency and aligns with the philosophy of natural language interaction. Users often want to "do something with that" after a command runs.

---

## Status Key

- [ ] Not started
- [x] Completed
- [~] In progress
