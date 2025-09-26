"""
MCP Container Manager for detecting and connecting to running MCP servers
"""

import subprocess
import json
import re
from typing import Dict, Any, Optional, List


class MCPContainerManager:
    """Manages connections to MCP server containers"""
    
    # Known MCP server container patterns
    MCP_CONTAINER_PATTERNS = [
        r".*mcp.*kubernetes.*",
        r".*kubernetes.*mcp.*",
        r".*vscode.*mcp.*server.*",
        r".*mcp.*server.*k8s.*",
        r".*ghcr\.io/azure/mcp-kubernetes.*",
        r".*mcp.*"  # More general pattern as fallback
    ]
    
    def __init__(self):
        self.cached_container_info = None
        self.cache_timestamp = 0
        
    def find_running_container(self) -> Optional[Dict[str, Any]]:
        """
        Find running MCP Kubernetes server container
        
        Returns:
            Dictionary with container info or None if not found
        """
        try:
            # Get list of running containers
            result = subprocess.run([
                "docker", "ps", "--format", 
                '{"id":"{{.ID}}", "image":"{{.Image}}", "names":"{{.Names}}", "status":"{{.Status}}", "ports":"{{.Ports}}"}'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f"Docker ps failed: {result.stderr}")
                return None
            
            containers = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        container = json.loads(line)
                        containers.append(container)
                    except json.JSONDecodeError as e:
                        print(f"Failed to parse container JSON: {line} - {e}")
                        continue
            
            print(f"Found {len(containers)} running containers")
            
            # Look for MCP server containers
            for container in containers:
                print(f"Checking container: {container.get('names', '')} - {container.get('image', '')}")
                if self._is_mcp_kubernetes_container(container):
                    print(f"Container matches MCP pattern!")
                    # Check if container is healthy
                    if self.is_container_healthy(container['id']):
                        return {
                            'container_id': container['id'],
                            'name': container['names'],
                            'image': container['image'],
                            'status': container['status'],
                            'ports': container['ports']
                        }
                    else:
                        print(f"Container {container['id']} is not healthy")
            
            print("No matching MCP containers found")
            return None
            
        except Exception as e:
            print(f"Error finding MCP container: {e}")
            return None
    
    def _is_mcp_kubernetes_container(self, container: Dict[str, Any]) -> bool:
        """Check if container matches MCP Kubernetes server patterns"""
        
        # Check image and names against known patterns
        check_fields = [container.get('image', ''), container.get('names', '')]
        
        for field in check_fields:
            for pattern in self.MCP_CONTAINER_PATTERNS:
                if re.search(pattern, field.lower()):
                    return True
        
        # Additional check for VS Code MCP servers (common case)
        if 'vscode' in container.get('image', '').lower():
            # Check if it has MCP-related environment or labels
            try:
                inspect_result = subprocess.run([
                    "docker", "inspect", container['id']
                ], capture_output=True, text=True, timeout=5)
                
                if inspect_result.returncode == 0:
                    inspect_data = json.loads(inspect_result.stdout)
                    if inspect_data and len(inspect_data) > 0:
                        config = inspect_data[0].get('Config', {})
                        env_vars = config.get('Env', [])
                        labels = config.get('Labels', {})
                        
                        # Check for MCP-related environment variables or labels
                        for env_var in env_vars:
                            if 'mcp' in env_var.lower() or 'kubernetes' in env_var.lower():
                                return True
                        
                        for label_key, label_value in labels.items():
                            if 'mcp' in f"{label_key} {label_value}".lower():
                                return True
            except:
                pass
        
        return False
    
    def is_container_healthy(self, container_id: str) -> bool:
        """
        Check if container is healthy and responsive
        
        Args:
            container_id: Docker container ID
            
        Returns:
            True if container is healthy
        """
        try:
            # First check if container is actually running
            result = subprocess.run([
                "docker", "inspect", container_id, 
                "--format", "{{.State.Status}}"
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return False
                
            status = result.stdout.strip()
            if status != 'running':
                return False
            
            # Try a simple exec to see if container is responsive
            exec_result = subprocess.run([
                "docker", "exec", container_id, "echo", "health_check"
            ], capture_output=True, text=True, timeout=5)
            
            return exec_result.returncode == 0 and "health_check" in exec_result.stdout
            
        except Exception:
            return False
    
    def get_connection_info(self, container_id: str) -> Optional[Dict[str, Any]]:
        """
        Get connection information for MCP server
        
        Args:
            container_id: Docker container ID
            
        Returns:
            Connection info dictionary or None
        """
        try:
            result = subprocess.run([
                "docker", "inspect", container_id
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return None
            
            inspect_data = json.loads(result.stdout)
            if not inspect_data or len(inspect_data) == 0:
                return None
            
            container_info = inspect_data[0]
            network_settings = container_info.get('NetworkSettings', {})
            ports = network_settings.get('Ports', {})
            
            # Extract port mappings
            port_mappings = {}
            for container_port, host_bindings in ports.items():
                if host_bindings:
                    port_mappings[container_port] = host_bindings[0].get('HostPort')
            
            return {
                'container_id': container_id,
                'ip_address': network_settings.get('IPAddress', ''),
                'ports': port_mappings,
                'environment': container_info.get('Config', {}).get('Env', [])
            }
            
        except Exception as e:
            print(f"Error getting connection info: {e}")
            return None