"""
Specialized context management for AI queries.
This module contains context definitions for different domains and utilities for matching queries to contexts.
"""

# SSH context keywords and definition
ssh_keywords = [
    'ssh', 'remote', 'login', 'connect', 'master', 'server', 'scp', 'rsync',
    'sftp', 'rsh', 'passwordless', 'public key', 'private key'
]

ssh_context = [
    {
        "role": "system",
        "content": "When generating SSH commands that need to execute commands on the remote server, always use the format: ssh hostname \"command1 && command2\" with the remote commands in quotes. Never use the format: ssh hostname && command1 && command2. Use ssh keys when possible and suggest setting up key authentication if it seems the user is typing passwords frequently. Consider connection persistence with ControlMaster for multiple connections."
    }
]

# Git context keywords and definition
git_keywords = [
    'git', 'commit', 'branch', 'merge', 'clone', 'pull', 'push', 'checkout',
    'rebase', 'fetch', 'stash', 'tag', 'cherry-pick', 'reset', 'reflog'
]

git_context = [
    {
        "role": "system",
        "content": "When answering Git-related questions, prioritize modern Git commands and workflows. Suggest best practices for branching, merging, and resolving conflicts. Favor commands that are safe and reversible when possible."
    }
]

# Network context keywords and definition
network_keywords = [
    'network', 'ping', 'ifconfig', 'ip addr', 'netstat', 'curl', 'wget', 'dns',
    'nslookup', 'dig', 'traceroute', 'tcpdump', 'wireshark', 'subnet', 'route',
    'firewall', 'iptables', 'nftables', 'bridge', 'tunnel', 'proxy'
]

network_context = [
    {
        "role": "system",
        "content": "For networking commands, balance between powerful diagnostic tools and user-friendly output. Consider security implications of network commands and suggest appropriate permissions or warnings when needed."
    }
]

# Python context keywords and definition
python_keywords = [
    'python', 'pip', 'venv', 'virtualenv', 'django', 'flask', 'pandas', 'numpy',
    'matplotlib', 'scikit', 'pytorch', 'tensorflow', 'jupyter', 'conda', 'poetry',
    'pytest', 'unittest', 'pdb', 'pyenv', 'requirements.txt', 'setup.py', 'wheel',
    '.py', 'def', 'class', 'import', 'from', 'asyncio', 'fastapi', 'sqlalchemy'
]

python_context = [
    {
        "role": "system",
        "content": "For Python-related commands and code, prioritize modern Python practices and PEP standards. Suggest type hints for function signatures, use f-strings for string formatting, and favor context managers for resource handling. Recommend virtual environments for package management and appropriate testing frameworks. When showing examples, include proper error handling and docstrings. For command-line tools, explain common flags and environment variables that affect Python behavior."
    }
]

# Kubernetes context keywords and definition
kubernetes_keywords = [
    'kubernetes', 'k8s', 'kubectl', 'pod', 'deployment', 'service', 'ingress',
    'namespace', 'helm', 'kube', 'minikube', 'cluster', 'node', 'configmap',
    'secret', 'statefulset', 'daemonset', 'persistent volume', 'pv', 'pvc'
]

def get_kubernetes_context():
    """
    Get Kubernetes context with tool preference based on availability.
    Prefers MCP Kubernetes tools when available, except for interactive exec commands.
    """
    from app.tools import ToolRegistry
    
    # Check if MCP Kubernetes tools are available
    available_tools = ToolRegistry.get_all_tools()
    mcp_k8s_tools = [name for name in available_tools.keys() if name.startswith('k8s_')]
    
    if mcp_k8s_tools:
        # MCP Kubernetes tools are available - prefer them
        tool_list = ', '.join(mcp_k8s_tools)
        return [
            {
                "role": "system",
                "content": f"""For Kubernetes-related commands and queries, PRIORITIZE using the specialized MCP Kubernetes tools over the generic linux_command tool. 

Available MCP Kubernetes tools: {tool_list}

IMPORTANT: When displaying tool results, show the literal output from kubectl commands rather than summarizing. Users want to see the actual pod names, statuses, resource details, etc. Only summarize if the output is extremely long or the user specifically asks for a summary.

EXCEPTION - Interactive kubectl exec commands: For interactive kubectl exec sessions (like "log into", "exec into", "bash into", "shell into" a pod), ALWAYS use the linux_command tool instead of MCP tools. These commands require TTY support (-it flags) that MCP cannot provide. Use commands like "kubectl exec -it pod-name -- bash" directly through linux_command.

Use these MCP tools for kubectl operations instead of linux_command when possible, as they provide much richer analysis and structured output. Only fall back to linux_command for kubectl operations if the specific functionality isn't covered by the MCP tools or for interactive exec sessions.

For resource management, emphasize best practices like explicit namespace specification and proper YAML formatting. Consider using declarative configuration files for production environments."""
            }
        ]
    else:
        # No MCP tools available - use standard guidance
        return [
            {
                "role": "system", 
                "content": "For Kubernetes-related commands, emphasize best practices like explicit namespace specification, using kubectl explain for resource discovery, and proper resource management. Suggest kubectl shortcuts and common troubleshooting patterns. Recommend proper YAML formatting for resources, and consider using kubectl apply with declarative configuration files instead of imperative commands for production environments."
            }
        ]

kubernetes_context = get_kubernetes_context()

# Directory navigation context keywords and definition
cd_keywords = [
    'cd', 'change directory', 'navigate', 'go to', 'move to', 'enter directory',
    'switch to', 'chdir', 'cd into', 'navigate to'
]

cd_context = [
    {
        "role": "system",
        "content": "For directory navigation requests, ALWAYS use the linux_command tool with the 'cd' command to actually change directories. Finding a directory path is only the first step - you must then use 'cd' to navigate to it. When a user asks to 'go to', 'navigate to', or 'change to' a directory, execute the appropriate 'cd' command. You can chain commands like 'cd $(find . -name dirname -type d | head -1)' or use separate tool calls: first find the directory, then cd to it. The current working directory changes only when you execute a 'cd' command."
    }
]

# Dictionary to map specialized contexts to their keywords
context_map = {
    'ssh': {'keywords': ssh_keywords, 'context': ssh_context},
    'git': {'keywords': git_keywords, 'context': git_context},
    'network': {'keywords': network_keywords, 'context': network_context},
    'python': {'keywords': python_keywords, 'context': python_context},
    'kubernetes': {'keywords': kubernetes_keywords, 'context': get_kubernetes_context},
    'cd': {'keywords': cd_keywords, 'context': cd_context}
}

def add_specialized_contexts(command, base_context):
    """
    Analyze a command and add specialized contexts based on keyword matching.
    
    Args:
        command (str): The user command or query
        base_context (list): The base context to extend with specialized contexts
        
    Returns:
        list: The extended context with any matching specialized contexts added
    """
    if not command or not isinstance(command, str):
        return base_context
        
    # Convert to lowercase for case-insensitive matching
    command_lower = command.lower()
    
    # Check each context for matching keywords
    for context_type, context_data in context_map.items():
        if any(keyword in command_lower for keyword in context_data['keywords']):
            context_content = context_data['context']
            # Handle both static lists and dynamic functions
            if callable(context_content):
                context_content = context_content()
            base_context.extend(context_content)
    
    return base_context

# Temperature adjustment based on command characteristics
def determine_temperature(command):
    """
    Determine the appropriate temperature setting based on the command type.
    
    Args:
        command (str): The user command or query
        
    Returns:
        float: The temperature value to use (between 0 and 1)
    """
    # if the OPEN_API_MODEL contains "GPT-5", return 1.0 since thismodel does not support temperature adjustment
    # get the env variable OPEN_API_MODEL
    import os
    OPEN_API_MODEL = os.getenv("OPEN_API_MODEL")
    if "gpt-5" in OPEN_API_MODEL.lower():
        return 1.0
    
    if not command or not isinstance(command, str):
        return 0.5  # Default temperature
        
    command_lower = command.lower()
    
    # Creative keywords should be checked first as they take precedence
    # Use higher temperature for more creative tasks
    if any(term in command_lower for term in 
          ['script', 'create', 'generate', 'design', 'write']):
        return 0.7
    
    # Then check for technical keywords which need precision
    if any(keyword in command_lower for keyword in 
          git_keywords + kubernetes_keywords + python_keywords + ['config', 'ssh']):
        return 0.3
    
    # Default temperature for other queries
    return 0.5
