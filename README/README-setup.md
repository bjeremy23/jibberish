# Setting up AI Credentials for Jibberish

This guide explains how to set up the credentials required to use Jibberish shell with different AI providers.

## Setting up Azure OpenAI Credentials

To use the Jibberish shell with Azure OpenAI, you'll need to set up the following credentials in your `~/.jbrsh` file:

1. **AZURE_OPENAI_API_KEY** - Your Azure OpenAI API key
2. **AZURE_OPENAI_ENDPOINT** - Your Azure OpenAI service endpoint URL
3. **AZURE_OPENAI_API_VERSION** - The Azure OpenAI API version to use (e.g., "2023-05-15")
4. **AZURE_OPENAI_DEPLOYMENT_NAME** - The name of your deployed model (e.g., "gpt-4.1")

### How to obtain Azure OpenAI credentials:

1. **Create an Azure account**: If you don't have an Azure account yet, sign up at [https://azure.microsoft.com](https://azure.microsoft.com).

2. **Request access to Azure OpenAI**: Azure OpenAI is currently available by application only. Apply for access at [https://aka.ms/oai/access](https://aka.ms/oai/access).

3. **Create an Azure OpenAI resource**:
   - Log in to the [Azure Portal](https://portal.azure.com)
   - Search for "Azure OpenAI" and select it
   - Click "Create"
   - Fill in the required details (resource name, subscription, resource group, region)
   - Click "Review + create", then "Create"

4. **Deploy a model**:
   - Go to your newly created Azure OpenAI resource
   - Select "Model deployments" from the left menu
   - Click "Create new deployment"
   - Select a model (e.g., "gpt-4", "gpt-4.1")
   - Set a deployment name (you'll use this as AZURE_OPENAI_DEPLOYMENT_NAME)
   - Configure other settings as needed
   - Click "Create"

5. **Get your credentials**:
   - From your Azure OpenAI resource page, go to "Keys and Endpoint"
   - Copy one of the keys (either KEY1 or KEY2) for AZURE_OPENAI_API_KEY
   - Copy the Endpoint URL for AZURE_OPENAI_ENDPOINT
   - For AZURE_OPENAI_API_VERSION, use the latest stable version (e.g., "2023-05-15")

6. **Add credentials to ~/.jbrsh**:
   ```
   AZURE_OPENAI_API_KEY="your-api-key-here"
   AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com/"
   AZURE_OPENAI_API_VERSION="2023-05-15"
   AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment-name"
   ```

**Note**: Keep your API key secure and never share it publicly.

### Using Entra ID authentication instead of key-based authentication

To avoid the use of an API key, Jibberish supports authentication via Azure AD (Entra ID) methods and RBAC role assignment.  Both Managed Identity and Azure CLI interactive login are supported.

#### Managed Identity of System-Assigned Identity
When running Jibberish in an Azure virtual machine, it is recommended to use the system-assigned identity or user-assigned managed identity of the VM resource to authenticate usage of Azure OpenAI.  The steps to utilize a managed identity are:

1. **Ensure your Managed Identity in Azure is assigned RBAC roles on the Azure OpenAI resource**
   - Assign the Managed Identity/System Identity the "Cognitive Services OpenAI User" role on the Open AI instance
     
2. **Configure the ~/.jbrsh file**
   - Remove/comment the variable ```AZURE_OPENAI_API_KEY```
   - Add the variable ```AZURE_CLIENT_ID``` with the value of the client_id of the managed identity
   ```
   #AZURE_OPENAI_API_KEY="your-api-key-here"
   AZURE_CLIENT_ID="your-managed-identity-client-id-here"
   ```
#### Azure CLI interactive login
Jibberish supports interactive Azure CLI login for authentication.

1. **Ensure your user ID is assigned RBAC roles on the Azure OpenAI resource**
   - Assign your user identity the "Cognitive Services OpenAI User" role on the Open AI instance
     
2. **Configure the ~/.jbrsh file**
   - Remove/comment the variable ```AZURE_OPENAI_API_KEY```
   - Add the variable ```AZURE_USER_NAME``` with the value of the user name you are using for login
   ```
   #AZURE_OPENAI_API_KEY="your-api-key-here"
   AZURE_USER_NAME="your-username@domein.com"
   ```

## Setting up OpenAI Credentials

As an alternative to Azure OpenAI, you can directly use OpenAI's services. You'll need to set up the following credentials in your `~/.jbrsh` file:

1. **OPEN_API_KEY** - Your OpenAI API key
2. **OPEN_API_MODEL** - The OpenAI model to use (e.g., "gpt-4", "gpt-4-turbo", "gpt-4o")

### How to obtain OpenAI credentials:

1. **Create an OpenAI account**: Sign up at [https://platform.openai.com/signup](https://platform.openai.com/signup).

2. **Get your API key**:
   - Log in to your OpenAI account at [https://platform.openai.com](https://platform.openai.com)
   - Click on your profile icon in the top-right corner
   - Select "View API keys"
   - Click "Create new secret key"
   - Give your key a name (optional) and click "Create"
   - Copy your API key (you won't be able to see it again)

3. **Choose a model**:
   - OpenAI offers various models with different capabilities and pricing
   - Common choices include:
     - `gpt-4` - Most powerful reasoning and instruction following
     - `gpt-4-turbo` - Faster version of GPT-4 with updated knowledge
     - `gpt-4o` - The latest GPT-4 model with improved performance
     - `gpt-3.5-turbo` - Faster and more cost-effective for simpler tasks

4. **Add credentials to ~/.jbrsh**:
   ```
   OPEN_API_KEY="your-openai-api-key-here"
   OPEN_API_MODEL="gpt-4"
   ```

5. **Set up billing**:
   - Go to [https://platform.openai.com/account/billing/overview](https://platform.openai.com/account/billing/overview)
   - Add a payment method
   - Set up usage limits to control costs (recommended)

**Note**: OpenAI API usage incurs costs based on your usage. Monitor your usage to avoid unexpected charges.
