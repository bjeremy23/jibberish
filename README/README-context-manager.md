# Context Manager for Jibberish

The `context_manager.py` module provides specialized context management for AI queries in the Jibberish shell environment.

## Purpose

This module centralizes the management of:
- Domain-specific contexts (SSH, Git, Kubernetes, Networking)
- Keyword detection for domain matching
- Temperature adjustment based on query type

## Functions

### `add_specialized_contexts(command, base_context)`

Analyzes a command and adds domain-specific contexts to the base context based on keyword matching.

Example usage:
```python
from context_manager import add_specialized_contexts

# Start with base context
context = [{"role": "system", "content": "Base system prompt"}]

# Add specialized contexts based on user command
command = "How do I clone a git repository?"
enhanced_context = add_specialized_contexts(command, context)
# enhanced_context now includes Git-specific guidance
```

### `determine_temperature(command)`

Determines the appropriate temperature setting for the AI model based on the command type:
- Technical commands: 0.3 (more precise)
- Creative tasks: 0.7 (more creative)
- Other queries: 0.5 (balanced)

Example usage:
```python
from context_manager import determine_temperature

command = "git commit my changes"
temp = determine_temperature(command)  # Returns 0.3 for technical command
```

## Extending with New Domains

To add a new specialized domain:

1. Define a keyword list for the domain
2. Create the context definition
3. Add both to the `context_map` dictionary

Example:
```python
# Define keywords
python_keywords = ['python', 'pip', 'virtualenv', 'django', 'flask']

# Define context
python_context = [{
    "role": "system",
    "content": "For Python-related commands, favor modern practices..."
}]

# Add to context map
context_map['python'] = {
    'keywords': python_keywords, 
    'context': python_context
}
```
