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
from app.utils import generate_tool_context_message, is_debug_enabled

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
# we have a total of 10 questions and keep the last 6 questions in the history
# These are global variables to keep track of the number of questions
total_noof_questions=10
noof_questions=6

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
    
    # Instead of appending the entire chat as a separate conversation,
    # we want to maintain one continuous conversation
    if not chat_history:
        # First conversation - save as is
        chat_history = chat
    else:
        # Ongoing conversation - extend the existing history
        # Remove any duplicate messages that might already be in history
        new_messages = []
        for msg in chat:
            # Only add messages that aren't already in the last few messages of history
            if len(chat_history) == 0 or msg not in chat_history[-5:]:
                new_messages.append(msg)
        
        chat_history.extend(new_messages)
        
        # Keep only the most recent message pairs (limit to total_noof_questions pairs)
        if len(chat_history) > total_noof_questions * 2:
            # Remove the oldest pairs to maintain the limit
            excess_messages = len(chat_history) - (total_noof_questions * 2)
            chat_history = chat_history[excess_messages:]

def load_chat_history():
    """
    Load chat from the global history, returning the recent conversation messages
    """
    global chat_history
    
    # Return the current conversation history
    # We want the last noof_questions pairs (each pair is 2 entries: user + assistant)
    if not chat_history:
        return []
    
    # Limit to the most recent conversation pairs
    max_messages = noof_questions * 2  # 2 messages per pair (user + assistant)
    if len(chat_history) > max_messages:
        return chat_history[-max_messages:]
    else:
        return chat_history


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
    Uses a two-phase approach: first execute tools, then generate response with tool context.
    """
    return _ask_question_with_tools(command, temp, max_tool_iterations=4)

def _ask_question_with_tools(command, temp=0.5, max_tool_iterations=4):
    """
    Internal function that handles the tool execution loop.
    Phase 1: Execute any initial tool calls from AI response
    Phase 2: Generate final response using tool outputs
    """
    original_command = command
    tool_context = []  # Accumulate tool outputs
    
    # Load the current conversation history at the start
    messages = load_chat_history()
    
    for iteration in range(max_tool_iterations):
        # Debug: Show iteration info
        if is_debug_enabled():
            click.echo(click.style(f"[DEBUG] Tool iteration {iteration + 1}/{max_tool_iterations}", fg="cyan"))
        
        # Add additional context for certain types of questions
        additional_context = []
        if any(term in command.lower() for term in ['technical', 'explain', 'how does', 'why is']):
            additional_context.append({
                "role": "system",
                "content": f"Provide accurate technical explanations while maintaining the character of {partner}."
            })
        
        # Add tool availability context for all iterations (not just iteration 0)
        tool_context_msg = generate_tool_context_message()
        if tool_context_msg:
            additional_context.append(tool_context_msg)
        
        # Detect urgent write commands and force immediate action
        urgent_write_patterns = ['write the file', 'write it now', '!!!', 'immediately', 'better be done']
        if any(pattern in command.lower() for pattern in urgent_write_patterns) and tool_context:
            additional_context.append({
                "role": "system",
                "content": "URGENT: The user is demanding immediate file writing. You MUST use write_file tool NOW with the content you have. Do not read more files. Use this exact format: ```json\n{\"tool_calls\": [{\"name\": \"write_file\", \"arguments\": {\"filepath\": \"path\", \"content\": \"merged_content\"}}]}\n```"
            })
        
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
        
        # Debug: Show the AI response
        if is_debug_enabled():
            click.echo(click.style(f"[DEBUG] AI Response: {ai_response}", fg="yellow"))
        
        # Check if the AI wants to use tools
        should_use = TOOLS_AVAILABLE and ToolCallParser.should_use_tools(ai_response)
        
        # Debug: Show tool detection
        if is_debug_enabled():
            click.echo(click.style(f"[DEBUG] Should use tools: {should_use}", fg="yellow"))
        
        if should_use:
            tool_calls = ToolCallParser.extract_tool_calls(ai_response)
            
            # Debug: Show extracted tool calls
            if is_debug_enabled():
                click.echo(click.style(f"[DEBUG] Tool calls extracted: {len(tool_calls) if tool_calls else 0}", fg="yellow"))
                if tool_calls:
                    for i, tool_call in enumerate(tool_calls):
                        click.echo(click.style(f"[DEBUG] Tool {i+1}: {tool_call.get('name', 'unknown')}", fg="yellow"))
            
            if tool_calls:
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
                    # Clean up the AI response that contained the tool calls before proceeding
                    if TOOLS_AVAILABLE:
                        import re
                        # Only remove JSON blocks containing tool_calls
                        ai_response = re.sub(r'```json\s*\n.*?"tool_calls".*?```', '', ai_response, flags=re.IGNORECASE | re.DOTALL)
                        ai_response = re.sub(r'\n{2,}', '\n\n', ai_response.strip())
                    
                    # Add the current interaction to the conversation history before continuing
                    messages.append(current_message)
                    messages.append({
                        "role": "assistant", 
                        "content": ai_response if ai_response.strip() else f"[Tool execution: {', '.join([tc.get('name', 'unknown') for tc in tool_calls])}]"
                    })
                    
                    # Save intermediate conversation state so follow-up questions can see tool results
                    save_chat(messages)
                    
                    # For the next iteration, provide the tool outputs and ask for final response
                    command = f"Based on the tool outputs above, provide your final answer to: {original_command}"
                    if is_debug_enabled():
                        click.echo(click.style(f"[DEBUG] Continuing to next iteration with command: {command[:100]}...", fg="cyan"))
                    continue  # Go to next iteration with tool context
        
        # No tools in response - we're done, exit the loop
        if is_debug_enabled():
            click.echo(click.style(f"[DEBUG] No tools found in response, exiting loop", fg="cyan"))
        break
    
    # Clean up response by removing tool call syntax if present
    if TOOLS_AVAILABLE:
        import re
        # Only remove JSON blocks containing tool_calls, not all JSON
        ai_response = re.sub(r'```json\s*\n.*?"tool_calls".*?```', '', ai_response, flags=re.IGNORECASE | re.DOTALL)
        # Clean up excessive newlines and whitespace
        ai_response = re.sub(r'\n{2,}', '\n\n', ai_response.strip())
    
    # Ensure we return clean response
    ai_response = ai_response.strip()
    
    # Add final conversation to history
    messages.append(current_message)
    messages.append({
        "role": "assistant", 
        "content": ai_response
    })
    save_chat(messages)
    return ai_response




