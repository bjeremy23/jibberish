import api, time, click, re, json

chat_file_path = "/tmp/jibberish.txt"
n =3 # number of lines to return

global_context = [
    {
        "role": "system",
        "content": "You are a Linux guru, who uses very few words to answer the question."
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
    messages = global_context + base_messages.copy()

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
        return response.choices[0].message.content.strip()
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


