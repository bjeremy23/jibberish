# MCP Server Configuration

## Overview

Jibberish supports connecting to multiple MCP (Model Context Protocol) servers to extend its capabilities. MCP servers provide tools and resources that the AI can use to perform various tasks.

## Important: Server Discovery vs. Starting

**Jibberish discovers existing MCP servers - it does NOT start them automatically.**

You are responsible for:
- Starting MCP servers before launching Jibberish
- Ensuring servers are running and accessible
- Managing server lifecycles (starting, stopping, restarting)

Jibberish will:
- Discover configured servers on startup
- Validate connectivity (for URL-based servers)
- Connect to servers per-request (for Docker/local processes)
- Register available tools from each server

## Configuration File

MCP servers are configured through a dedicated JSON file at `~/.jbrsh-mcp-servers.json`.

**Example:**
```json
{
  "kubernetes": {
    "enabled": true,
    "command": "docker",
    "args": [
      "run", "-i", "--rm",
      "-v", "~/.kube/config:/home/mcp/.kube/config",
      "ghcr.io/azure/mcp-kubernetes",
      "--access-level", "readwrite"
    ],
    "description": "Kubernetes cluster management and kubectl operations",
    "tool_prefix": "k8s"
  },
  "test": {
    "enabled": true,
    "command": "python3",
    "args": ["/path/to/simple_mcp_server.py"],
    "description": "Simple test MCP server",
    "tool_prefix": "test"
  }
}
```

## Server Types

### 1. Docker Containers

Run MCP servers in Docker containers. These are spawned per-request with `docker run -i --rm`.

**Configuration:**
```json
{
  "server_name": {
    "enabled": true,
    "command": "docker",
    "args": [
      "run", "-i", "--rm",
      "-v", "/path/to/config:/container/path",
      "ghcr.io/org/mcp-server-image",
      "--server-arg", "value"
    ],
    "description": "Server description",
    "tool_prefix": "prefix"
  }
}
```

**Key Points:**
- Use `docker` as the command
- Include `run -i --rm` in args for interactive, temporary containers
- Mount necessary volumes for configuration/data access
- Container is started fresh for each tool call

### 2. Local Executables

Run MCP servers as local processes (Python scripts, Node.js, binaries, etc.).

**Configuration:**
```json
{
  "server_name": {
    "enabled": true,
    "command": "python3",
    "args": ["/absolute/path/to/mcp_server.py"],
    "env": {
      "CUSTOM_VAR": "value"
    },
    "description": "Local Python MCP server",
    "tool_prefix": "local"
  }
}
```

**Examples:**
- Python: `"command": "python3", "args": ["/path/to/server.py"]`
- Node.js with npx: `"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home"]`
- uvx: `"command": "uvx", "args": ["mcp-server-git", "--repository", "/path/to/repo"]`

**Key Points:**
- Use absolute paths to executables and scripts
- Process is spawned per-request
- Set environment variables via `env` property if needed

### 3. URL-Based Servers

Connect to remote MCP servers via HTTP/HTTPS.

**Configuration:**
```json
{
  "server_name": {
    "enabled": true,
    "command": "https://mcp-server.example.com/api",
    "description": "Remote MCP server",
    "tool_prefix": "remote"
  }
}
```

**Key Points:**
- Use full URL (http:// or https://) as the command
- No args needed
- Server must be running and accessible before Jibberish starts
- JSON-RPC requests sent via HTTP POST

## Configuration Properties

### Required Properties

- **`command`**: The command to execute or URL to connect to
  - Docker: `"docker"`
  - Local: absolute path to executable (e.g., `"python3"`, `"/usr/bin/node"`)
  - URL: full HTTP/HTTPS URL

### Optional Properties

- **`enabled`**: `true` or `false` (default: `true`)
  - Set to `false` to temporarily disable a server without removing its configuration

- **`args`**: Array of command-line arguments (default: `[]`)
  - Used for Docker and local executables
  - Ignored for URL-based servers

- **`env`**: Object with environment variable key-value pairs (default: `{}`)
  - Only used for Docker and local executables
  - Example: `{"HOME": "/custom/home", "DEBUG": "true"}`

- **`description`**: Human-readable description (default: `""`)
  - Helps document what the server does

- **`tool_prefix`**: Prefix for tool names from this server (default: server name)
  - This is an internal tag used to separate toolsets into individual namespaces
  - Prevents naming conflicts when multiple MCP servers provide tools with the same name
  - Tools will be named `{prefix}_{tool_name}` in Jibberish's registry
  - The prefix is stripped before calling the actual MCP server
  - Can be any arbitrary string that makes sense for organization
  - Example: `"k8s"` → tools named `k8s_kubectl_get`, `k8s_kubectl_apply`, etc.

## Server Lifecycle Management

### Starting Servers

**Before launching Jibberish**, ensure your MCP servers are:

1. **Docker containers**: Either pre-running or configured to be spawned per-request (recommended)
2. **Local processes**: Available as executables with proper permissions
3. **URL servers**: Running and accessible at the configured endpoint

### Per-Request Spawning (Docker/Local)

For Docker and local servers, Jibberish spawns a new process for each tool call:
- Process starts when tool is invoked
- JSON-RPC request sent via stdin
- Response read from stdout
- Process terminates after response

This approach ensures:
- Clean state for each request
- No long-running process management
- Automatic resource cleanup

### Long-Running Servers (URL)

For URL-based servers:
- Server must be running continuously
- Jibberish sends HTTP POST requests per tool call
- You manage the server lifecycle independently

## Example Configurations

### Example 1: Kubernetes MCP Server (Docker)

```json
{
  "kubernetes": {
    "enabled": true,
    "command": "docker",
    "args": [
      "run", "-i", "--rm",
      "-v", "~/.kube/config:/home/mcp/.kube/config",
      "ghcr.io/azure/mcp-kubernetes",
      "--access-level", "readwrite"
    ],
    "description": "Kubernetes cluster management and kubectl operations",
    "tool_prefix": "k8s"
  }
}
```

### Example 2: Simple Test Server (Local Python)

```json
{
  "test": {
    "enabled": true,
    "command": "python3",
    "args": [
      "/home/brownjer/bin/jibberish/tests/simple_mcp_server.py"
    ],
    "description": "Simple test MCP server with echo and add tools",
    "tool_prefix": "test"
  }
}
```

### Example 3: Filesystem Server (Node.js via npx)

```json
{
  "filesystem": {
    "enabled": true,
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-filesystem",
      "/home"
    ],
    "description": "File system operations and management",
    "tool_prefix": "fs"
  }
}
```

### Example 4: Git Server (Python via uvx)

```json
{
  "git": {
    "enabled": true,
    "command": "uvx",
    "args": [
      "mcp-server-git",
      "--repository",
      "/path/to/repo"
    ],
    "description": "Git repository operations",
    "tool_prefix": "git"
  }
}
```

### Example 5: Remote HTTP Server

```json
{
  "remote_api": {
    "enabled": true,
    "command": "https://api.example.com/mcp",
    "description": "Remote MCP API server",
    "tool_prefix": "api"
  }
}
```

## Troubleshooting

### Server Not Discovered

**Symptoms:** "No MCP servers configured or enabled" message

**Solutions:**
1. Check that `~/.jbrsh-mcp-servers.json` exists and is valid JSON
2. Verify `enabled: true` for the server
3. Ensure `command` property is set
4. Check file permissions

### Tools Not Registered

**Symptoms:** Server discovered but no tools available

**Solutions:**
1. Verify the server is actually running (for URL-based)
2. Check server logs/output for errors
3. Enable debug mode: `JIBBERISH_DEBUG=true` in `~/.jbrsh`
4. Test server manually:
   ```bash
   echo '{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}' | python3 /path/to/server.py
   ```

### Docker Container Errors

**Symptoms:** "Failed to discover MCP server" for Docker containers

**Solutions:**
1. Verify Docker is installed and running
2. Check that the image exists: `docker pull ghcr.io/org/image`
3. Verify volume mounts are correct and accessible
4. Test manually: `docker run -i --rm ghcr.io/org/image`

### Permission Errors (Local Executables)

**Symptoms:** "Permission denied" when starting local server

**Solutions:**
1. Make script executable: `chmod +x /path/to/server.py`
2. Verify shebang line: `#!/usr/bin/env python3`
3. Check that command exists: `which python3`

## Testing Your Configuration

### 1. Create a Simple Test Server

Use the included test server at `tests/simple_mcp_server.py`:

```json
{
  "test": {
    "enabled": true,
    "command": "python3",
    "args": ["<LOCAL_PATH>/jibberish/tests/simple_mcp_server.py"],
    "tool_prefix": "test"
  }
}
```

### 2. Enable Debug Mode

Add to `~/.jbrsh`:
```bash
JIBBERISH_DEBUG=true
```

### 3. Launch Jibberish

```bash
jibberish
```

Look for output like:
```
Loaded 2 MCP server configurations (2 enabled)
Discovering 2 enabled MCP servers
Discovering MCP server 'test' (type: local)
Local MCP server 'test' configured: python3 /path/to/simple_mcp_server.py
Discovered 2 MCP servers
Registering tools for MCP server: test (local)
Registered 2 tools from MCP server 'test'
```

### 4. Test Tools

In Jibberish:
```bash
? Use test_echo to say hello
? Use test_add to add 5 and 3
```

## Additional Resources

- MCP Protocol Specification: https://modelcontextprotocol.io
- Example MCP Servers: https://github.com/modelcontextprotocol/servers
- Kubernetes MCP Server: https://github.com/Azure/mcp-kubernetes
- Jibberish Documentation: See `README/` directory

## Template Configuration

Copy this to `~/.jbrsh-mcp-servers.json` to get started:

```json
{
  "example_docker": {
    "enabled": false,
    "command": "docker",
    "args": [
      "run", "-i", "--rm",
      "ghcr.io/org/mcp-server-image"
    ],
    "description": "Example Docker MCP server",
    "tool_prefix": "docker"
  },
  "example_local": {
    "enabled": false,
    "command": "python3",
    "args": ["/path/to/mcp_server.py"],
    "description": "Example local MCP server",
    "tool_prefix": "local"
  },
  "example_url": {
    "enabled": false,
    "command": "https://mcp-server.example.com/api",
    "description": "Example URL MCP server",
    "tool_prefix": "url"
  }
}
```

Enable the servers you want by setting `"enabled": true` and updating the configuration values.
