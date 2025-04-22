import os, openai

# Define version information
__version__ = "25.04.0"
VERSION_NAME = "Initial Release"

# openai
with open(os.path.expanduser("~/.jbrsh")) as env:
    for line in env:
        line = line.strip()
        # Skip empty lines or comments
        if not line or line.startswith("//") or line.startswith("#"):
            continue
        # Only try to split if there's an equal sign
        if "=" in line:
            key, value = line.split("=", 1)  # Split only on the first =
            # Remove quotes if present
            value = value.strip('"\'')
            os.environ[key.strip()] = value
            print(f"Set {key.strip()} to {value.strip()}")
    print("Environment variables loaded from ~/.jbrsh\n")

ai_choice = os.environ.get('AI_CHOICE', 'openai').lower()
if ai_choice not in ["openai", "azure"]:
    raise ValueError("Invalid AI_CHOICE. Must be 'openai' or 'azure'.")

# azure 
if ai_choice == "azure":
    openai.api_type = "azure"
    openai.api_base = os.environ['AZURE_OPENAI_ENDPOINT']
    openai.api_version = os.environ['AZURE_OPENAI_API_VERSION']
    openai.api_key = os.environ['AZURE_OPENAI_API_KEY']
    model = os.environ ['AZURE_OPENAI_DEPLOYMENT_NAME']  # <-- Replace with your actual deployment name
else:
    client = openai.OpenAI(
        api_key=os.environ['OPEN_API_KEY']
    )
    model = "gpt-4"


