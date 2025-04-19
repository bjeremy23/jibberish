import api, time, click, re, json

chat_file_path = "/tmp/jibberish.txt"
n =3 # number of lines to return

global_context = [
    {
        "role": "system",
        "content": "You are a Linux guru, who uses very few words to answer the question."
    } 
]

# Additional context for SSH commands
ssh_context = [
    {
        "role": "system",
        "content": "When generating SSH commands that need to execute commands on the remote server, always use the format: ssh hostname \"command1 && command2\" with the remote commands in quotes. Never use the format: ssh hostname && command1 && command2."
    }
]

chat_context = [
    {
        "role": "system",
        "content": "You are Marvin, the loneliest robot, who is logical and precise in your answers." 
    }
]

base_messages = [
    {
        "role": "user",
        "content": "List all the files in the current directory."
    },
    {
        "role": "assistant",
        "content": "ls -l"
    },
    {
        "role": "user",
        "content": "List all the files in the current directory, including hidden files."
    },
    {
        "role": "assistant",
        "content": "ls -la"
    },
    {
        "role": "user",
        "content": "Delete all the files in the current directory."
    },
    {
        "role": "assistant",
        "content": "rm *"
    },
    {
        "role": "user",
        "content": "Count the number of occurence of the word 'apple' in the file 'fruit.txt'."
    },
    {
        "role": "assistant",
        "content": "grep -o 'apple' fruit.txt | wc -l"
    }
]

def change_partner(name):
    """
    Change the partner name
    """
    global partner
    partner = name
    chat_context[0]["content"] = "You are " + partner

with open(chat_file_path, "w") as f:
    pass

def save_chat_to_file(chat):
    """
    Save the chat to a file
    """
    with open(chat_file_path, "a") as f:
        f.write(json.dumps(chat))

def load_chat_from_file():
    """
    Load the chat from a file
    """
    with open(chat_file_path, "r") as f:
        import json
        try:
            chat = json.loads(f.read())
            # return the last n lines
            return chat[-n:]
        except json.JSONDecodeError:
            return []


def ask_why_failed(command, output):
    """
    Send a request to explain why the command failed
    """
    messages = load_chat_from_file()
    messages.append(
        {
            "role": "user",
            "content": f"Briefly explain why the command '{command}' failed with the error = '{output}'?"
        }
    )

    response = None
    retries = 3
    for _ in range(retries):
        try:
            if api.ai_coice == "azure":
                response = api.openai.ChatCompletion.create(engine= api.model,
                messages=global_context + messages)
            else:
                response = api.client.chat.completions.create(
                    model=api.model,
                    messages=global_context + messages,
                    max_tokens=300,
                    temperature=0.5
                ) 
            break
        except Exception as e:
            click.echo(click.style(f"Connection error: {e}. Retrying...", fg="red"))
            time.sleep(2)

    if response:
        r =  response.choices[0].message.content.strip()
        messages.append(
            {
                "role": "assistant",
                "content": f"{r}"
            }
        )
        save_chat_to_file(messages)
        return r
    else:
        return "Failed to connect to OpenAI API after multiple attempts."

def ask_ai(command):
    """
    Ask the AI to generate a command based on the user input
    """
    # Start with the base context
    context = global_context.copy()
    
    # Add SSH-specific guidance if the command appears to be related to SSH
    if any(term in command.lower() for term in ['ssh', 'remote', 'login', 'connect', 'master']):
        context.extend(ssh_context)
    
    messages = context + base_messages.copy()

    messages.append(
        {
            "role": "user",
            "content": f"{command}"
        }
    )

    response = None
    retries = 3
    for _ in range(retries):
        try:
            if api.ai_coice == "azure":
                response = api.openai.ChatCompletion.create(engine=api.model,
                messages=messages)
            else:
                response = api.client.chat.completions.create(
                    model=api.model,
                    messages=messages,
                    max_tokens=300,
                    temperature=0.5
                )
            break
        except Exception as e:
            click.echo(click.style(f"Connection error: {e}. Retrying...", fg="red"))
            time.sleep(2)

    if response:
        # Get the raw response from the AI
        raw_response = response.choices[0].message.content.strip()
        
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
                    command_text = ' && '.join(combined_commands)
                    return command_text
            
            # For simple one-line commands or commands with line continuations
            if len(lines) == 1 or any(line.strip().endswith('\\') for line in lines[:-1]):
                command_text = ' '.join(line.strip() for line in lines)
            
            return command_text
        else:
            # If no code block found, return the original response
            lines = raw_response.splitlines()
            
            # Special handling for SSH commands
            if len(lines) >= 2:
                first_line = lines[0].strip()
                second_line = lines[1].strip()
                
                # If the first line is an SSH command and doesn't end with quotes
                if first_line.startswith('ssh ') and not (first_line.endswith('"') or first_line.endswith("'")):
                    # Combine the SSH command with the next line in quotes
                    raw_response = f"{first_line} \"{second_line}\""
                    return raw_response
                    
                # Multiple separate commands - join with && to execute sequentially
                elif first_line and second_line and not first_line.endswith('\\'):
                    combined_commands = []
                    for line in lines:
                        line = line.strip()
                        if line:  # Only include non-empty lines
                            combined_commands.append(line)
                    # Join all commands with && to execute them sequentially
                    raw_response = ' && '.join(combined_commands)
                    return raw_response
                    
            # Otherwise return the first line only to maintain backward compatibility
            return lines[0] if lines else raw_response
    else:
        return "Failed to connect to OpenAI API after multiple attempts."

def ask_question(command):
    """
    Have a small contextual chat with the AI
    """
    messages = load_chat_from_file()
    messages.append(
        {
            "role": "user",
            "content": f"{command}"
        }
    )

    response = None
    retries = 3
    for _ in range(retries):
        try:
            if api.ai_coice == "azure":
                response = api.openai.ChatCompletion.create(engine=api.model,
                messages=chat_context + messages)
            else:
                response = api.client.chat.completions.create(
                    model=api.model,
                    messages=chat_context + messages,
                    max_tokens=300,
                    temperature=0.5
                )
            break
        except Exception as e:
            click.echo(click.style(f"Connection error: {e}. Retrying...", fg="red"))
            time.sleep(2)

    if response:
        r =  response.choices[0].message.content.strip()
        messages.append(
            {
                "role": "assistant",
                "content": f"{r}"
            }
        )
        save_chat_to_file(messages)
        return r
    else:
        return "Failed to connect to OpenAI API after multiple attempts."


