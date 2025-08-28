"""
Chat functionality for the jibberish shell environment.

This module handles all interactions with the AI:
- ask_ai: Generates shell commands based on natural language input
- ask_question: Has conversational exchanges with the AI in a chat-like manner
- ask_why_failed: Explains why a command failed

The AI context management (specialized domains and keyword detection) is handled by
the context_manager.py module, which provides functions for adding specialized 
contexts based on command keywords.
"""

from app import api
import time 
import click 
import re
import os
from app.context_manager import add_specialized_contexts, determine_temperature

# Import the tool system
try:
    from app.tools import ToolRegistry
    from app.tools.base import ToolCallParser
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False
    click.echo(click.style("Warning: Tool system not available", fg="yellow"))

# Get the default partner from environment variable or use the fallback
partner = os.environ.get('AI_PARTNER', "Marvin the Paranoid Android")

# There are two different histories; one for '#' (ask_ai) and one for '?' (ask_question)

# '?' 
# we have a total of 10 questions and keep the last 3 questions in the history
# These are global variables to keep track of the number of questions
total_noof_questions=10
noof_questions=3

# Global list to store chat history for each instance of the shell
chat_history = []

# '#'
# we have a maximum of 4 pairs of messages (user/assistant) in the command history 
MAX_HISTORY_PAIRS = 4

# Global context for the AI
global_context = [
    {
        "role": "system",
        "content": "You are a Linux guru with extensive command line expertise. Provide concise, efficient commands that solve the user's problem. Favor modern tools and include brief explanations only when necessary. Format commands for easy copy-paste usage. Consider security implications and use best practices."
    } 
]

# Context for the chat with the partner
chat_context = [
    {
        "role": "system",
        "content": f"You are {partner}. You are brilliant, logical, precise and factual in your answers. Ensure your responses match the personality and style of {partner}. Your information should always be accurate and helpful."
    }
]

# Initialize with example messages that will be kept within the 4-pair limit
base_messages = [
    {
        "role": "user",
        "content": "List all files in the current directory sorted by modification time, with the newest first."
    },
    {
        "role": "assistant",
        "content": "ls -lt"
    },
    {
        "role": "user",
        "content": "Find all Python files in the current directory and subdirectories that contain the word 'error'."
    },
    {
        "role": "assistant",
        "content": "find . -name \"*.py\" -type f -exec grep -l \"error\" {} \\;"
    },
    {
        "role": "user",
        "content": "Monitor system resource usage and show the top processes consuming CPU and memory."
    },
    {
        "role": "assistant",
        "content": "top -o %CPU"
    },
    {
        "role": "user",
        "content": "Create a backup of all text files in my project, compress them, and add a timestamp to the archive name."
    },
    {
        "role": "assistant",
        "content": "find ./project -name \"*.txt\" | tar -czvf backup_$(date +%Y%m%d_%H%M%S).tar.gz -T -"
    }
]

def change_partner(name):
    """
    Change the partner name
    """
    global partner
    partner = name
    chat_context[0]["content"] = f"You are {partner}. You are brilliant, logical, precise and factual in your answers. Ensure your responses match the personality and style of {partner}. Your information should always be accurate and helpful."

# Use os module for file operations

# No need to initialize a file anymore - we're using a global list

def save_chat(chat):
    """
    Save the chat by updating the global chat history
    """
    global chat_history
    
    # Add current conversation
    chat_history.append(chat)
    
    # Keep only the most recent conversations
    chat_history = chat_history[-total_noof_questions:]

def load_chat_history():
    """
    Load chat from the global history, returning only the most recent noof_questions entries (user/assistant pairs)
    """
    global chat_history
    
    # If there's no history yet, return empty list
    if not chat_history:
        return []
        
    # If we have history, return the last conversation's entries limited to noof_questions
    if chat_history and isinstance(chat_history[-1], list):
        last_conversation = chat_history[-1]
        # We want the last noof_questions pairs (each pair is 2 entries)
        message_pairs = len(last_conversation) // 2
        pairs_to_keep = min(noof_questions, message_pairs)
        # Calculate how many entries to skip from the beginning
        entries_to_skip = len(last_conversation) - (pairs_to_keep * 2)
        return last_conversation[entries_to_skip:]
    
    return []


def ask_why_failed(command, output):
    """
    Send a request to explain why the command failed
    """
    messages = load_chat_history()
    messages.append(
        {
            "role": "user",
            "content": f"Briefly explain why the command '{command}' failed with the error = '{output}'?"
        }
    )

    # Set temperature
    temperature = 0.5
    
    try:
        # Handle both new and legacy Azure OpenAI APIs
        if hasattr(api.client, 'chat'):
            # New OpenAI API (v1.0.0+)
            response = api.client.chat.completions.create(
                model=api.model,
                messages=messages,
                temperature=temperature
            )
        else:
            # Legacy OpenAI API (pre-v1.0.0)
            response = api.client.ChatCompletion.create(
                engine=api.model,  # For Azure legacy API, use engine instead of model
                messages=messages,
                temperature=temperature
            )
            
        return response.choices[0].message.content.strip()
    except Exception as e:
        click.echo(click.style(f"Error when explaining command failure: {e}", fg="red"))
        return None

def find_similar_command(command_name):
    """
    Find a similar command when a command is not found
    Args:
        command_name (str): The command that was not found
    Returns:
        str: A suggestion for a similar command, or None if no suggestions
    """
    messages = [
        {
            "role": "system",
            "content": "You are a Linux command expert. When given a misspelled or invalid command, suggest the most likely correct command. Respond with ONLY the corrected command, nothing else."
        },
        {
            "role": "user",
            "content": f"I tried to run the command '{command_name}' but it wasn't found. What's the most likely correct command? Respond with ONLY the command name."
        }
    ]
    
    # Determine temperature based on query type
    temperature = 0.5
    
    try:
        # Handle both new and legacy Azure OpenAI APIs
        if hasattr(api.client, 'chat'):
            # New OpenAI API (v1.0.0+)
            response = api.client.chat.completions.create(
                model=api.model,
                messages=messages,
                temperature=temperature
            )
        else:
            # Legacy OpenAI API (pre-v1.0.0)
            response = api.client.ChatCompletion.create(
                engine=api.model,  # For Azure legacy API, use engine instead of model
                messages=messages,
                temperature=temperature
            )
            
        # Extract the response content
        suggested_command = response.choices[0].message.content.strip()
        
        # If the suggested command is the same as the original, don't suggest it
        if suggested_command.lower() == command_name.lower():
            return None
            
        return suggested_command
    except Exception as e:
        click.echo(click.style(f"Error when finding similar command: {e}", fg="red"))
        return None
    
def ask_ai(command):
    """
    Ask the AI to generate a command based on the user input
    """
    # Declare global variable at the beginning of the function
    global base_messages
    
    # Start with the base context
    context = global_context.copy()
    
    # Use the context manager to add specialized contexts based on the command
    context = add_specialized_contexts(command, context)
    
    # Create a copy of base_messages to work with
    current_messages = base_messages.copy()
    
    # Add the current user query
    messages = context + current_messages.copy()
    
    messages.append(
        {
            "role": "user",
            "content": f"{command}"
        }
    )

    response = None
    retries = 3
    
    # Determine appropriate temperature based on query type using the context manager
    temperature = determine_temperature(command)
    
    for _ in range(retries):
        try:
            # Handle both new and legacy Azure OpenAI APIs
            if hasattr(api.client, 'chat'):
                # New OpenAI API (v1.0.0+)
                response = api.client.chat.completions.create(
                    model=api.model,
                    messages=messages,
                    temperature=temperature
                )
            else:
                # Legacy OpenAI API (pre-v1.0.0)
                response = api.client.ChatCompletion.create(
                    engine=api.model,  # For Azure legacy API, use engine instead of model
                    messages=messages,
                    temperature=temperature
                )
            break
        except Exception as e:
            click.echo(click.style(f"Connection error: {e}. Retrying...", fg="red"))
            time.sleep(2)

    if response:
        # Get the raw response from the AI
        raw_response = response.choices[0].message.content.strip()
        
        # Process the raw response to get the final command
        final_command = None
        
        # Remove markdown code block formatting if present
        # This handles patterns like ```bash\ncommand\n``` or ```\ncommand\n```
        code_block_pattern = r"```(?:bash|sh)?\s*([\s\S]*?)```"
        match = re.search(code_block_pattern, raw_response)
        if match:
            # Get the command inside the code block and handle possible newlines
            command_text = match.group(1).strip()
            
            # Process multiple lines of commands
            lines = command_text.splitlines()
            if len(lines) >= 2:
                # Handle multiple separate commands - join with && to execute sequentially locally
                if len(lines) >= 2:
                    combined_commands = []
                    for line in lines:
                        line = line.strip()
                        if line:  # Only include non-empty lines
                            combined_commands.append(line)
                    # Join all commands with && to execute them sequentially
                    final_command = ' && '.join(combined_commands)
                    
            # For simple one-line commands or commands with line continuations
            if len(lines) == 1 or any(line.strip().endswith('\\') for line in lines[:-1]):
                final_command = ' '.join(line.strip() for line in lines)
        else:
            # If no code block found, process the original response
            lines = raw_response.splitlines()
            
            # Special handling for SSH commands
            if len(lines) >= 2:
                first_line = lines[0].strip()
                second_line = lines[1].strip()
                
                # If the first line is an SSH command and doesn't end with quotes
                if first_line.startswith('ssh ') and not (first_line.endswith('"') or first_line.endswith("'")):
                    # Combine the SSH command with the next line in quotes
                    final_command = f"{first_line} \"{second_line}\""
                    
                # Multiple separate commands - join with && to execute sequentially
                elif first_line and second_line and not first_line.endswith('\\'):
                    combined_commands = []
                    for line in lines:
                        line = line.strip()
                        if line:  # Only include non-empty lines
                            combined_commands.append(line)
                    # Join all commands with && to execute them sequentially
                    final_command = ' && '.join(combined_commands)
            
            # Otherwise use the first line or the raw response
            if final_command is None:
                final_command = lines[0] if lines else raw_response
        
        
        # Add the new conversation pair
        new_pair = [
            {"role": "user", "content": command},
            {"role": "assistant", "content": final_command}
        ]
        
        # Add new messages to the base messages
        base_messages.extend(new_pair)
        
        # If we now have more than MAX_HISTORY_PAIRS (4) pairs, trim the oldest ones
        if len(base_messages) > MAX_HISTORY_PAIRS * 2:
            # Remove the oldest pairs (2 messages per pair) to maintain the limit
            excess_pairs = (len(base_messages) - MAX_HISTORY_PAIRS * 2) // 2
            base_messages = base_messages[excess_pairs * 2:]
        
        return final_command
    else:
        return "Failed to connect to OpenAI API after multiple attempts."

def ask_question(command, temp=0.5):
    """
    Have a small contextual chat with the AI, with tool support.
    If the AI requests tools, execute them and resend with enhanced context.
    """
    return _ask_question_with_tools(command, temp, max_tool_iterations=3)

def _ask_question_with_tools(command, temp=0.5, max_tool_iterations=3):
    """
    Internal function that handles the tool execution loop.
    """
    original_command = command
    messages = load_chat_history()
    tool_context = []  # Accumulate tool outputs
    
    for iteration in range(max_tool_iterations):
        # Add additional context for certain types of questions
        additional_context = []
        if any(term in command.lower() for term in ['technical', 'explain', 'how does', 'why is']):
            additional_context.append({
                "role": "system",
                "content": f"Provide accurate technical explanations while maintaining the character of {partner}."
            })
        
        # Add tool availability context if tools are available
        if TOOLS_AVAILABLE and iteration == 0:
            available_tools = ToolRegistry.get_all_tools()
            if available_tools:
                tool_descriptions = []
                for tool_name, tool in available_tools.items():
                    tool_descriptions.append(f"- {tool_name}: {tool.description}")
                
                tool_context_msg = {
                    "role": "system", 
                    "content": f"""You have access to the following tools to help answer questions:

{chr(10).join(tool_descriptions)}

To use a tool, include in your response: TOOL_CALL: tool_name(param="value")
For example: TOOL_CALL: read_file(filepath="/path/to/file")

Use tools when you need additional information to provide a complete answer."""
                }
                additional_context.append(tool_context_msg)
        
        # Add any tool context from previous iterations
        if tool_context:
            context_msg = {
                "role": "system",
                "content": f"Additional context from tools:\n\n{chr(10).join(tool_context)}"
            }
            additional_context.append(context_msg)
        
        # Prepare the current message
        current_message = {
            "role": "user",
            "content": command
        }
        
        current_messages = messages + [current_message]
        
        response = None
        retries = 3
        
        # Use the context manager's temperature function, but default to the provided temp
        if temp == 0.5:  # Only override if default was used
            temp = determine_temperature(command)
            
        for _ in range(retries):
            try:
                # Handle both new and legacy Azure OpenAI APIs
                if hasattr(api.client, 'chat'):
                    # New OpenAI API (v1.0.0+)
                    response = api.client.chat.completions.create(
                        model=api.model,
                        messages=chat_context + additional_context + current_messages,
                        temperature=temp
                    )
                else:
                    # Legacy OpenAI API (pre-v1.0.0)
                    response = api.client.ChatCompletion.create(
                        engine=api.model,  # For Azure legacy API, use engine instead of model
                        messages=chat_context + additional_context + current_messages,
                        temperature=temp
                    )
                break
            except Exception as e:
                click.echo(click.style(f"Connection error: {e}. Retrying...", fg="red"))
                time.sleep(2)

        if not response:
            return "Failed to connect to OpenAI API after multiple attempts."
        
        ai_response = response.choices[0].message.content.strip()
        
        # Check if the AI wants to use tools
        if TOOLS_AVAILABLE and ToolCallParser.should_use_tools(ai_response):
            tool_calls = ToolCallParser.extract_tool_calls(ai_response)
            
            if tool_calls:
                click.echo(click.style(f"AI is requesting {len(tool_calls)} tool(s)...", fg="blue"))
                
                # Execute each tool call
                tools_executed = False
                for tool_call in tool_calls:
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("arguments", {})
                    
                    tool = ToolRegistry.get_tool(tool_name)
                    if tool:
                        click.echo(click.style(f"Executing tool: {tool_name}", fg="cyan"))
                        try:
                            tool_output = tool.execute(**tool_args)
                            tool_context.append(f"Tool {tool_name} output:\n{tool_output}")
                            tools_executed = True
                            click.echo(click.style(f"Tool {tool_name} completed", fg="green"))
                        except Exception as e:
                            error_msg = f"Tool {tool_name} failed: {str(e)}"
                            tool_context.append(error_msg)
                            click.echo(click.style(error_msg, fg="red"))
                    else:
                        error_msg = f"Tool {tool_name} not found"
                        tool_context.append(error_msg)
                        click.echo(click.style(error_msg, fg="red"))
                
                if tools_executed:
                    # Modify the command to include context about tool execution
                    command = f"{original_command}\n\nPlease provide a complete answer using the tool outputs above."
                    continue  # Go to next iteration with tool context
        
        # No more tools needed, return the final response
        messages.append(current_message)
        messages.append({
            "role": "assistant",
            "content": ai_response
        })
        save_chat(messages)
        return ai_response
    
    # If we've exhausted iterations, return what we have
    return ai_response if 'ai_response' in locals() else "Maximum tool iterations reached without completing the request."


