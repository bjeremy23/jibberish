# MCP Kubernetes Integration for Jibberish

This document explains how to set up and use the MCP (Model Context Protocol) Kubernetes server integration with Jibberish. This integration allows you to interact with Kubernetes clusters using natural language through Jibberish's AI-powered shell.

## Overview

The MCP Kubernetes integration provides:
- Natural language Kubernetes cluster queries
- Direct kubectl command execution through AI
- Kubernetes resource management and diagnostics
- Advanced cluster inspection and troubleshooting capabilities

Jibberish automatically detects when an MCP Kubernetes server is running locally and registers its tools for AI-powered Kubernetes interactions.

## Prerequisites

- Docker installed and running
- A Kubernetes cluster with `kubectl` configured
- Valid kubeconfig file (typically at `~/.kube/config`)
- Jibberish shell installed and configured

## Setup Instructions

### 1. Prepare Your Kubeconfig

Ensure your kubeconfig file is properly configured and accessible:

```bash
# Verify kubectl works
kubectl cluster-info

# Check your kubeconfig location
echo $KUBECONFIG
# or use default location: ~/.kube/config
```

### 2. Start the MCP Kubernetes Container

Run the MCP Kubernetes server as a Docker container. Jibberish looks for containers with specific naming patterns, so use the recommended container name:

#### Basic Setup (Read-Only Access)

```bash
docker run -d \
  --name mcp-kubernetes-server \
  --mount type=bind,src=$HOME/.kube/config,dst=/home/mcp/.kube/config \
  ghcr.io/azure/mcp-kubernetes:latest
```

#### Read-Write Access

```bash
docker run -d \
  --name mcp-kubernetes-server \
  --mount type=bind,src=$HOME/.kube/config,dst=/home/mcp/.kube/config \
  ghcr.io/azure/mcp-kubernetes:latest \
  --access-level readwrite
```

#### Full Admin Access

```bash
docker run -d \
  --name mcp-kubernetes-server \
  --mount type=bind,src=$HOME/.kube/config,dst=/home/mcp/.kube/config \
  ghcr.io/azure/mcp-kubernetes:latest \
  --access-level admin
```

#### With Additional Tools (Helm, Cilium, Hubble)

```bash
docker run -d \
  --name mcp-kubernetes-server \
  --mount type=bind,src=$HOME/.kube/config,dst=/home/mcp/.kube/config \
  ghcr.io/azure/mcp-kubernetes:latest \
  --access-level readwrite \
  --additional-tools helm,cilium,hubble
```

### 3. Verify Container is Running

```bash
# Check container status
docker ps | grep mcp-kubernetes

# Check container logs
docker logs mcp-kubernetes-server
```

### 4. Start Jibberish

When you start Jibberish, it will automatically detect the running MCP Kubernetes container and register the tools:

```bash
jibberish
```

You should see output indicating MCP tools were detected (if `JIBBERISH_DEBUG=true`):

```
Found MCP Kubernetes container: mcp-kubernetes-server
Registered 4 MCP Kubernetes tools  # (number varies by access level)
```

## Access Levels

The MCP Kubernetes server supports three access levels that determine available operations:

| Access Level | Description | Available Tools | Operations Allowed |
|--------------|-------------|-----------------|-------------------|
| `readonly` (default) | View-only access | 4 kubectl tools | get, describe, logs, events, etc. |
| `readwrite` | Read and write access | 6 kubectl tools | create, delete, apply, patch, etc. |
| `admin` | Full administrative access | 7+ kubectl tools | All operations including node management |

## Available Tools

Once the MCP server is running, Jibberish will have access to these Kubernetes tools:

### Core Tools (All Access Levels)
- **kubectl_cluster_info** - Get cluster information and API details
- **kubectl_cluster_resources** - View Kubernetes resources (get, describe)
- **kubectl_cluster_diagnostics** - Debug resources (logs, events, top)

### Additional Tools (Read-Write and Admin)
- **kubectl_workloads** - Manage deployments, pods, services
- **kubectl_metadata** - Manage ConfigMaps, Secrets, labels
- **kubectl_config** - Configuration and security operations

### Admin-Only Tools
- **kubectl_nodes** - Node management (cordon, drain, taint)

### Optional Additional Tools
- **helm** - Helm package manager commands
- **cilium** - Cilium CNI operations
- **hubble** - Hubble network observability

## Example Usage

### Basic Cluster Information

```bash
jibberish> what is the status of my kubernetes cluster?
```

This will use the MCP tools to check cluster health, node status, and overall cluster information.

### Pod Management

```bash
jibberish> show me all pods in the production namespace
```


```bash
jibberish> get the logs for the failing pod in kube-system
```

### Resource Inspection

```bash
jibberish> describe all deployments
```

```bash
jibberish> check resource usage across all nodes
```

```bash
jibberish> show me all services and their endpoints
```

### Troubleshooting

```bash
jibberish> why is my deployment not ready?
```

```bash
jibberish> check for any failing pods and show their events
```

```bash
jibberish> analyze the resource usage of my application pods
```

### Advanced Operations (Read-Write Access)

```bash
jibberish> scale my web deployment to 5 replicas
```

```bash
jibberish> create a configmap from this file
```

```bash
jibberish> restart the deployment in the staging namespace
```

## Tool Preference System

When MCP Kubernetes tools are available, Jibberish automatically prefers them over basic `linux_command` for Kubernetes operations. This provides:

- **Richer Context**: Tools provide structured data that the AI can better interpret
- **Better Error Handling**: More informative error messages and suggestions
- **Enhanced Capabilities**: Access to operations beyond basic kubectl commands
- **Namespace Awareness**: Automatic namespace context in responses

## Configuration Options

### Environment Variables

Set these when starting the container:

```bash
# Disable telemetry collection
-e KUBERNETES_MCP_COLLECT_TELEMETRY=false

# Custom kubeconfig location
-e KUBECONFIG=/path/to/your/kubeconfig
```

### Command-Line Arguments

Common options for the MCP server:

```bash
--access-level readonly|readwrite|admin    # Set permission level
--allow-namespaces ns1,ns2,ns3            # Restrict to specific namespaces
--additional-tools helm,cilium,hubble      # Enable additional tools
--timeout 120                              # Set command timeout (seconds)
```

### Example with Namespace Restrictions

```bash
docker run -d \
  --name mcp-kubernetes-server \
  --mount type=bind,src=$HOME/.kube/config,dst=/home/mcp/.kube/config \
  ghcr.io/azure/mcp-kubernetes:latest \
  --access-level readwrite \
  --allow-namespaces production,staging,development
```

## Troubleshooting

### Container Not Detected

If Jibberish doesn't detect the MCP container:

1. **Check container name**: Ensure it matches the pattern Jibberish looks for:
   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}" | grep -i kubernetes
   ```

2. **Verify container is running**:
   ```bash
   docker logs mcp-kubernetes-server
   ```

3. **Enable debug mode**:
   ```bash
   export JIBBERISH_DEBUG=true
   jibberish
   ```

### Permission Issues

If you get permission errors:

1. **Check kubeconfig permissions**:
   ```bash
   ls -la ~/.kube/config
   ```

2. **Verify kubectl works outside container**:
   ```bash
   kubectl get nodes
   ```

3. **Check container kubeconfig**:
   ```bash
   docker exec mcp-kubernetes-server kubectl get nodes
   ```

### Tool Registration Issues

If tools aren't registered:

1. **Check container logs**:
   ```bash
   docker logs mcp-kubernetes-server
   ```

2. **Restart Jibberish** after ensuring container is healthy

3. **Manually test container**:
   ```bash
   docker exec -it mcp-kubernetes-server kubectl version
   ```

## Security Considerations

- **Access Levels**: Start with `readonly` and increase permissions as needed
- **Namespace Restrictions**: Use `--allow-namespaces` to limit scope
- **Network Security**: The container runs locally and doesn't expose ports
- **Kubeconfig Access**: The container has the same cluster access as your local kubectl

## Stopping the MCP Server

To stop the MCP Kubernetes server:

```bash
# Stop and remove container
docker stop mcp-kubernetes-server
docker rm mcp-kubernetes-server

# Restart Jibberish to update tool registry
jibberish
```

## Advanced Usage

### Multiple Clusters

You can run multiple MCP servers for different clusters:

```bash
# Production cluster
docker run -d \
  --name mcp-k8s-production \
  --mount type=bind,src=$HOME/.kube/config-prod,dst=/home/mcp/.kube/config \
  ghcr.io/azure/mcp-kubernetes:latest \
  --access-level readonly

# Development cluster  
docker run -d \
  --name mcp-k8s-development \
  --mount type=bind,src=$HOME/.kube/config-dev,dst=/home/mcp/.kube/config \
  ghcr.io/azure/mcp-kubernetes:latest \
  --access-level readwrite
```

### Custom Tool Integration

The MCP integration in Jibberish is designed to be extensible. The system automatically discovers and registers tools from any running MCP Kubernetes container.

## Resources

- [MCP Kubernetes GitHub Repository](https://github.com/Azure/mcp-kubernetes)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Documentation](https://docs.docker.com/)

## Support

For issues related to:
- **MCP Kubernetes Server**: [GitHub Issues](https://github.com/Azure/mcp-kubernetes/issues)
- **Jibberish Integration**: [Jibberish Repository](https://github.com/bjeremy23/jibberish/issues)
- **General Kubernetes**: [Kubernetes Community](https://kubernetes.io/community/)