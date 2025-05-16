import os
import openai
from contextlib import redirect_stdout

# Import version information from centralized version module
from app.version import __version__, VERSION_NAME
from app.utils import silence_stdout, is_debug_enabled

# Load environment variables - always load them, but only print if debug is enabled
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
                if is_debug_enabled():
                    print(f"Environment variable {key}={value}")
            else:
                # Standard processing for other variables - remove quotes if present
                value = value.strip('"\'')
                os.environ[key] = value
                if is_debug_enabled():
                    print(f"Set {key} to {value}")
    
    if is_debug_enabled():
        print("Environment variables loaded from ~/.jbrsh\n")

ai_choice = os.environ.get('AI_CHOICE', 'openai').lower()
if ai_choice not in ["openai", "azure"]:
    raise ValueError("Invalid AI_CHOICE. Must be 'openai' or 'azure'.")

# azure 
if ai_choice == "azure":
    with silence_stdout():
        try:
            # Try importing AzureOpenAI class (available in v1.0.0+)
            from openai import AzureOpenAI
            
            # Determine the authentication method based on available credentials
            auth_method = None
            token_provider = None
            
            if os.environ.get('AZURE_CLIENT_ID'):
                try:
                    from azure.identity import ManagedIdentityCredential, get_bearer_token_provider
                    credential = ManagedIdentityCredential(client_id=os.environ['AZURE_CLIENT_ID'])
                    auth_method = "managed_identity"
                    token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
                    print("Using Azure Managed Identity authentication")
                except (ImportError, Exception) as e:
                    print(f"Could not use Managed Identity: {e}")
                    auth_method = None
            elif os.environ.get('AZURE_USER_ID'):
                try:
                    from azure.identity import AzureCliCredential, get_bearer_token_provider
                    credential = AzureCliCredential()
                    auth_method = "user_credential"
                    token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
                    print("Using Azure CLI credential authentication")
                except (ImportError, Exception) as e:
                    print(f"Could not use Azure CLI credentials: {e}.  Please ensure you are logged in to Azure CLI prior to running Jibberish.")
                    auth_method = None
            elif os.environ.get('AZURE_OPENAI_API_KEY'):
                auth_method = "key"
                print("Using API key authentication")
            else:
                auth_method = None
                raise ValueError("No valid authentication method available. Please provide AZURE_CLIENT_ID, AZURE_USER_ID, or AZURE_OPENAI_API_KEY.")
            
            # Create the appropriate client based on authentication method
            if auth_method in ["managed_identity", "user_credential"]:
                client = AzureOpenAI(
                    api_version=os.environ['AZURE_OPENAI_API_VERSION'],
                    azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT'],
                    azure_ad_token_provider=token_provider
                )
            else:  # key-based auth
                client = AzureOpenAI(
                    api_key=os.environ['AZURE_OPENAI_API_KEY'],
                    api_version=os.environ['AZURE_OPENAI_API_VERSION'],
                    azure_endpoint=os.environ['AZURE_OPENAI_ENDPOINT']
                )
            
            # For Azure, we use the deployment name as the model name
            model = os.environ['AZURE_OPENAI_DEPLOYMENT_NAME']
            print(f"Using AzureOpenAI client (v1.0.0+) with {auth_method} authentication for model {model}")
            
        except AttributeError as e:
            if is_debug_enabled():
                print(f"Error initializing AzureOpenAI client: {e}")
            # Fallback to standard client with key-based auth only
            if os.environ.get('AZURE_OPENAI_API_KEY'):
                client = openai.OpenAI(api_key=os.environ['AZURE_OPENAI_API_KEY'])
                model = os.environ['AZURE_OPENAI_DEPLOYMENT_NAME']
            else:
                raise ValueError("Cannot use managed identity or user credentials with legacy OpenAI client. Please provide AZURE_OPENAI_API_KEY.")
                
        except ImportError:
            # Use legacy Azure configuration (pre-v1.0.0)
            if is_debug_enabled():
                print("Using legacy OpenAI Azure configuration (pre-v1.0.0)")
            openai.api_type = "azure"
            
            # Can only use key-based auth with legacy client
            if not os.environ.get('AZURE_OPENAI_API_KEY'):
                raise ValueError("Legacy OpenAI client requires AZURE_OPENAI_API_KEY. Managed identity and user credentials are not supported.")
            
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
    model =  os.environ['OPEN_API_MODEL']

