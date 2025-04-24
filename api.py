import os, openai

# Define version information
__version__ = "25.04.2"
VERSION_NAME = "Bengal Release"

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
            key = key.strip()
            
            # Special handling for GIT_CONFIG_PARAMETERS which needs quoted value
            if key == "GIT_CONFIG_PARAMETERS":
                # Extract the actual value while preserving inner quotes
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]  # Remove outer double quotes only
                os.environ[key] = value
                print(f"Environment variable {key}={value}")
            else:
                # Standard processing for other variables - remove quotes if present
                value = value.strip('"\'')
                os.environ[key] = value
                print(f"Set {key} to {value}")
    print("Environment variables loaded from ~/.jbrsh\n")

ai_choice = os.environ.get('AI_CHOICE', 'openai').lower()
if ai_choice not in ["openai", "azure"]:
    raise ValueError("Invalid AI_CHOICE. Must be 'openai' or 'azure'.")

# azure 
if ai_choice == "azure":
    try:
        # Try importing AzureOpenAI class (available in v1.0.0+)
        from openai import AzureOpenAI
        try:
            # Use new client for Azure (v1.0.0+)
            client = AzureOpenAI(
                api_key=os.environ['AZURE_OPENAI_API_KEY'],
                api_version=os.environ['AZURE_OPENAI_API_VERSION'],
                azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT']
            )
            # For Azure, we use the deployment name as the model name
            model = os.environ['AZURE_OPENAI_DEPLOYMENT_NAME']
            print("Using AzureOpenAI client (v1.0.0+)")
        except (AttributeError) as e:
            print(f"Error initializing AzureOpenAI client: {e}")
            # Fallback to standard client
            client = openai.OpenAI(api_key=os.environ['AZURE_OPENAI_API_KEY'])
            model = os.environ['AZURE_OPENAI_DEPLOYMENT_NAME']
    except ImportError:
        # Use legacy Azure configuration (pre-v1.0.0)
        print("Using legacy OpenAI Azure configuration (pre-v1.0.0)")
        openai.api_type = "azure"
        openai.api_key = os.environ['AZURE_OPENAI_API_KEY']
        openai.api_base = os.environ['AZURE_OPENAI_ENDPOINT']
        openai.api_version = os.environ['AZURE_OPENAI_API_VERSION']
        client = openai
        model = os.environ['AZURE_OPENAI_DEPLOYMENT_NAME']
else:
    # Standard OpenAI client
    client = openai.OpenAI(
        api_key=os.environ['OPEN_API_KEY']
    )
    model = "gpt-4"


