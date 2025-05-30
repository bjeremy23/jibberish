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

kubernetes_context = [
    {
        "role": "system", 
        "content": "For Kubernetes-related commands, emphasize best practices like explicit namespace specification, using kubectl explain for resource discovery, and proper resource management. Suggest kubectl shortcuts and common troubleshooting patterns. Recommend proper YAML formatting for resources, and consider using kubectl apply with declarative configuration files instead of imperative commands for production environments."
    }
]

# Dictionary to map specialized contexts to their keywords
context_map = {
    'ssh': {'keywords': ssh_keywords, 'context': ssh_context},
    'git': {'keywords': git_keywords, 'context': git_context},
    'network': {'keywords': network_keywords, 'context': network_context},
    'python': {'keywords': python_keywords, 'context': python_context},
    'kubernetes': {'keywords': kubernetes_keywords, 'context': kubernetes_context}
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
            base_context.extend(context_data['context'])
    
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
