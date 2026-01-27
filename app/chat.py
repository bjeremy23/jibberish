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
from app.utils import (
    generate_tool_context_message, 
    is_debug_enabled,
    save_chat,
    load_chat_history,
    get_base_messages,
    update_base_messages
)
from app.output_history import (
    get_output_context_for_ai,
    has_output_reference,
    parse_output_reference,
    get_last_output
)

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

# Maximum number of message pairs to keep in command history
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
        "content": f"You are a Linux guru with extensive command line expertise. "
                  f"Provide concise, efficient commands that solve the user's problem. "
                  f"Favor modern tools and include brief explanations only when necessary. "
                  f"Consider security implications and use best practices. "
                  f"Your information should always be accurate and helpful. "
                  f"Any response with a linux command should call the linux_command tool "
                  f"with a concise, efficient command that solve the user's problem. "
                  f"Ensure your responses match the personality and style of {partner}."
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
    OPEN_API_MODEL = os.getenv("OPEN_API_MODEL")
    if OPEN_API_MODEL and "gpt-5" in OPEN_API_MODEL.lower():
        temperature = 1.0
    else:
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
    temperature = 1.0
    
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
    # Start with the base context
    context = global_context.copy()
    
    # Use the context manager to add specialized contexts based on the command
    context = add_specialized_contexts(command, context)
    
    # Check if user is referencing previous command outputs
    # Keywords like "that", "those", "the output", "from above" suggest output reference
    output_keywords = ['that', 'those', 'the output', 'from above', 'previous', 'last output', 
                       'the result', 'these files', 'those files', '$_', '@0', '@1', '@2', '@3']
    needs_output_context = any(kw in command.lower() for kw in output_keywords) or has_output_reference(command)
    
    # Add output history context if there are references or contextual keywords
    if needs_output_context:
        output_context = get_output_context_for_ai(max_entries=3)
        if output_context:
            context.append({
                "role": "system",
                "content": f"The user may be referring to previous command outputs. Here is the recent output history:\n\n{output_context}\n\nUse this context to understand what 'that', 'those', 'the output', etc. refer to."
            })
    
    # Create a copy of base_messages from utils to work with
    current_messages = get_base_messages().copy()
    
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
        
        # Sanitize command: remove any remaining newlines/carriage returns that could cause
        # "syntax error: unexpected end of file" in bash when executed
        final_command = final_command.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
        # Collapse multiple spaces into one
        final_command = ' '.join(final_command.split())
        
        # Add the new conversation pair
        new_pair = [
            {"role": "user", "content": command},
            {"role": "assistant", "content": final_command}
        ]
        
        # Add new messages to the base messages using utils function
        current_base = get_base_messages()
        current_base.extend(new_pair)
        
        # If we now have more than MAX_HISTORY_PAIRS (4) pairs, trim the oldest ones
        if len(current_base) > MAX_HISTORY_PAIRS * 2:
            # Remove the oldest pairs (2 messages per pair) to maintain the limit
            excess_pairs = (len(current_base) - MAX_HISTORY_PAIRS * 2) // 2
            current_base = current_base[excess_pairs * 2:]
        
        # Update the base messages
        update_base_messages(current_base)
        
        return final_command
    else:
        return "Failed to connect to OpenAI API after multiple attempts."

def _build_additional_context(command, partner, tool_context):
    """
    Build additional context messages for the AI based on command type and previous tool outputs.
    
    Args:
        command: The user command
        partner: The AI partner name  
        tool_context: List of previous tool outputs
        
    Returns:
        list: Additional context messages for the AI
    """
    additional_context = []
    
    # Add technical explanation context for certain question types
    if any(term in command.lower() for term in ['technical', 'explain', 'how does', 'why is']):
        additional_context.append({
            "role": "system",
            "content": f"Provide accurate technical explanations while maintaining the character of {partner}."
        })
    
    additional_context = add_specialized_contexts(command, additional_context)
    
    # Check if user is referencing previous command outputs
    output_keywords = ['that', 'those', 'the output', 'from above', 'previous', 'last output', 
                       'the result', 'these files', 'those files', '$_', '@0', '@1', '@2', '@3']
    needs_output_context = any(kw in command.lower() for kw in output_keywords) or has_output_reference(command)
    
    # Add output history context if there are references or contextual keywords
    if needs_output_context:
        output_context = get_output_context_for_ai(max_entries=3)
        if output_context:
            additional_context.append({
                "role": "system",
                "content": f"The user may be referring to previous command outputs. Here is the recent output history:\n\n{output_context}\n\nUse this context to understand what 'that', 'those', 'the output', etc. refer to."
            })
    
    # Add tool availability context
    tool_context_msg = generate_tool_context_message()
    if tool_context_msg:
        additional_context.append(tool_context_msg)
    
    # Detect urgent write commands and force immediate action
    urgent_write_patterns = ['write the file', 'write it now', '!!!', 'immediately']
    if any(pattern in command.lower() for pattern in urgent_write_patterns) and tool_context:
        additional_context.append({
            "role": "system",
            "content": "URGENT: The user is demanding immediate file writing. You MUST use write_file tool NOW with the content you have. Do not read more files. Use this exact format: ```json\n{\"tool_calls\": [{\"name\": \"write_file\", \"arguments\": {\"filepath\": \"path\", \"content\": \"merged_content\"}}]}\n```"
        })
    

    if tool_context:
        context_msg = {
            "role": "system",
            "content": f"Additional context from tools (for reference only - do NOT repeat):\n\n{chr(10).join(tool_context)}\n\nIMPORTANT: If the reulst are from linux_command_tool, just say 'done.' else summarize key findings, provide analysis, or proceed with the next action."
        }
        additional_context.append(context_msg)
        
        # Debug: Show what tool context is being added
        try:
            from app.utils import is_debug_enabled
            if is_debug_enabled():
                print(f"[DEBUG] Adding tool context: {len(tool_context)} items")
                for i, ctx in enumerate(tool_context):
                    print(f"[DEBUG] Context {i+1} length: {len(ctx)}")
                    print(f"[DEBUG] Context {i+1} preview: {ctx[:300]}...")
        except:
            pass  # Ignore debug errors
    
    return additional_context

def _get_ai_response(messages, additional_context, temp):
    """
    Get response from AI with retry logic.
    
    Args:
        messages: Conversation messages
        additional_context: Additional context for the AI
        temp: Temperature setting
        
    Returns:
        str or None: AI response content, or None if failed
    """
    response = None
    retries = 3
    
    for _ in range(retries):
        try:
            # Handle both new and legacy Azure OpenAI APIs
            if hasattr(api.client, 'chat'):
                # New OpenAI API (v1.0.0+)
                response = api.client.chat.completions.create(
                    model=api.model,
                    messages=chat_context + additional_context + messages,
                    temperature=temp
                )
            else:
                # Legacy OpenAI API (pre-v1.0.0)
                response = api.client.ChatCompletion.create(
                    engine=api.model,  # For Azure legacy API, use engine instead of model
                    messages=chat_context + additional_context + messages,
                    temperature=temp
                )
            break
        except KeyboardInterrupt:
            # Don't retry on Ctrl+C - just return None immediately
            return None
        except Exception as e:
            click.echo(click.style(f"Connection error: {e}. Retrying...", fg="red"))
            time.sleep(2)
    
    if not response:
        return None
        
    return response.choices[0].message.content.strip()

def _execute_tool_calls(tool_calls, tool_context):
    """
    Execute a list of tool calls and update the tool context.
    
    Args:
        tool_calls: List of tool call dictionaries
        tool_context: List to append tool outputs to
        
    Returns:
        bool: True if any tools were executed successfully
    """
    tools_executed = False
    
    for tool_call in tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("arguments", {})
        
        tool = ToolRegistry.get_tool(tool_name)
        if tool:
            if is_debug_enabled():
                click.echo(click.style(f"Executing tool: {tool_name} with args: {tool_args}", fg="cyan"))
                
            try:
                tool_output = tool.execute(**tool_args)
                tool_context.append(f"Tool {tool_name} output:\n{tool_output}")
                tools_executed = True
                click.echo(click.style(f"Tool {tool_name} completed", fg="green"))
            except KeyboardInterrupt:
                # Tool execution was interrupted - add info to context and re-raise
                error_msg = f"Tool {tool_name} cancelled by user"
                tool_context.append(error_msg)
                click.echo(click.style(error_msg, fg="yellow"))
                raise  # Re-raise to be caught by the calling function
            except Exception as e:
                error_msg = f"Tool {tool_name} failed: {str(e)}"
                tool_context.append(error_msg)
                click.echo(click.style(error_msg, fg="red"))
        else:
            error_msg = f"Tool {tool_name} not found"
            tool_context.append(error_msg)
            click.echo(click.style(error_msg, fg="red"))
    
    return tools_executed

def _clean_ai_response(ai_response):
    """
    Clean up AI response by removing tool call syntax.
    
    Args:
        ai_response: Raw AI response string
        
    Returns:
        str: Cleaned response
    """
    if TOOLS_AVAILABLE:
        import re
        # Only remove JSON blocks containing tool_calls
        ai_response = re.sub(r'```json\s*\n.*?"tool_calls".*?```', '', ai_response, flags=re.IGNORECASE | re.DOTALL)
        ai_response = re.sub(r'\n{2,}', '\n\n', ai_response.strip())
    
    return ai_response.strip()

def _update_conversation_history(messages, current_message, ai_response, tool_calls):
    """
    Update conversation history with current interaction.
    
    Args:
        messages: Current conversation messages
        current_message: The user's current message
        ai_response: The AI's response
        tool_calls: List of tool calls that were made
    """
    messages.append(current_message)
    messages.append({
        "role": "assistant", 
        "content": ai_response if ai_response.strip() else f"[Tool execution: {', '.join([tc.get('name', 'unknown') for tc in tool_calls])}]"
    })
    save_chat(messages)

def ask_question(command, temp=None):
    """
    Have a small contextual chat with the AI, with tool support.
    Uses a two-phase approach: first execute tools, then generate response with tool context.
    """
    return _ask_question_with_tools(command, temp, max_tool_iterations=6)

def _ask_question_with_tools(command, temp=None, max_tool_iterations=6):
    """
    Internal function that handles the tool execution loop.
    Phase 1: Execute any initial tool calls from AI response
    Phase 2: Generate final response using tool outputs
    """
    original_command = command
    tool_context = []  # Accumulate tool outputs
    
    # Load the current conversation history at the start
    messages = load_chat_history()

    try:
        for iteration in range(max_tool_iterations):
            # Debug: Show iteration info
            if is_debug_enabled():
                click.echo(click.style(f"[DEBUG] Tool iteration {iteration + 1}/{max_tool_iterations}", fg="cyan"))
            
            # Build additional context for this iteration
            global partner
            additional_context = _build_additional_context(command, partner, tool_context)
            
            # Prepare the current message
            current_message = {
                "role": "user",
                "content": command
            }
            
            current_messages = messages + [current_message]
            
            # Use the context manager's temperature function, but default to the provided temp
            if temp is None:  # Only override if default was used
                temp = determine_temperature(command)
            
            # add a debug to print the current message
            if is_debug_enabled():
                click.echo(click.style(f"[DEBUG] Current message: {current_message}", fg="yellow"))
                click.echo(click.style(f"[DEBUG] additional context: {additional_context}", fg="yellow"))

            # Get AI response
            ai_response = _get_ai_response(current_messages, additional_context, temp)
            if not ai_response:
                return "Failed to connect to OpenAI API after multiple attempts."
            

            
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
                    # Execute tool calls
                    try:
                        tools_executed = _execute_tool_calls(tool_calls, tool_context)
                    except KeyboardInterrupt:
                        click.echo()  # Print newline after ^C
                        click.echo(click.style("Tool execution cancelled by user", fg="yellow"))
                        return "Tool execution cancelled by user."
                    
                    if tools_executed:
                        # Clean up the AI response that contained the tool calls
                        ai_response = _clean_ai_response(ai_response)
                        
                        # Update conversation history
                        _update_conversation_history(messages, current_message, ai_response, tool_calls)
                        
                        # Reload messages from history to include the updated conversation
                        messages = load_chat_history()
                        
                        # Create a follow-up prompt that allows the AI to call more tools or display results
                        tools_used = [tc.get('name', 'unknown') for tc in tool_calls]
                        command = (
                            f"You have executed {', '.join(tools_used)} for the request '{original_command}'. "
                            "If you need to call more tools to complete the task, do so. "
                            "Otherwise, provide insights or analysis based on the tool outputs."
                        )
                        
                        if is_debug_enabled():
                            click.echo(click.style(f"[DEBUG] Tool context length: {len(tool_context)}", fg="cyan"))
                            click.echo(click.style(f"[DEBUG] Tool context preview: {tool_context[0][:200] if tool_context else 'empty'}...", fg="cyan"))
                            click.echo(click.style(f"[DEBUG] Continuing to next iteration with command: {command[:100]}...", fg="cyan"))
                        continue  # Go to next iteration with tool context
            
            # No tools in response - we're done, exit the loop
            if is_debug_enabled():
                click.echo(click.style(f"[DEBUG] No tools found in response, exiting loop", fg="cyan"))
            break
        
        # Clean up final response
        ai_response = _clean_ai_response(ai_response)
        
        # Add final conversation to history
        messages.append(current_message)
        messages.append({
            "role": "assistant", 
            "content": ai_response
        })
        save_chat(messages)
        return ai_response
    
    except KeyboardInterrupt:
        # Handle Ctrl+C during any part of the tool iteration loop
        click.echo()  # Print newline after ^C
        click.echo(click.style("Question processing cancelled by user", fg="yellow"))
        return "Operation cancelled by user."




