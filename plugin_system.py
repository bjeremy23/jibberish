"""
Plugin system for Jibberish built-in commands.
This module provides a registry and base classes for plugins.
"""
import os
import sys
import importlib
import pkgutil
import click
from abc import ABC, abstractmethod


class BuiltinCommand(ABC):
    """Base class for all built-in command plugins"""
    
    @abstractmethod
    def can_handle(self, command):
        """
        Check if this plugin can handle the given command.
        
        Args:
            command (str): The command to check
            
        Returns:
            bool: True if this plugin can handle the command, False otherwise
        """
        pass
    
    @abstractmethod
    def execute(self, command):
        """
        Execute the command.
        
        Args:
            command (str): The command to execute
            
        Returns:
            bool or tuple: 
                - True if the command was handled and execution should stop
                - False if the command was not handled
                - Tuple (False, new_command) if the plugin wants to return a new command for processing
        """
        pass


class BuiltinCommandRegistry:
    """Registry for built-in command plugins"""
    
    _plugins = []
    
    @classmethod
    def register(cls, plugin):
        """
        Register a plugin with the registry.
        
        Args:
            plugin: A BuiltinCommand instance
        """
        if not isinstance(plugin, BuiltinCommand):
            raise TypeError("Plugin must be an instance of BuiltinCommand")
        
        cls._plugins.append(plugin)
        click.echo(click.style(f"Registered plugin: {plugin.__class__.__name__}", fg="green"))
    
    @classmethod
    def find_handler(cls, command):
        """
        Find a plugin that can handle the given command.
        
        Args:
            command (str): The command to handle
            
        Returns:
            BuiltinCommand or None: The plugin that can handle the command, or None if no plugin can handle it
        """
        for plugin in cls._plugins:
            if plugin.can_handle(command):
                return plugin
        return None


def load_plugins():
    """
    Dynamically load all plugins from the plugins directory.
    """
    click.echo(click.style("Loading plugins...", fg="blue"))
    
    # Get the path to the plugins directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    plugins_dir = os.path.join(current_dir, "plugins")
    
    # Create plugins directory if it doesn't exist
    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir)
        click.echo(click.style(f"Created plugins directory: {plugins_dir}", fg="blue"))
    
    # Import all modules in the plugins package
    try:
        # Create an __init__.py file in the plugins directory if it doesn't exist
        init_file = os.path.join(plugins_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write("# This file marks the plugins directory as a Python package\n")
        
        # Import the plugins package
        plugins_package = importlib.import_module("plugins")
        
        # Load all modules in the plugins package
        for _, name, is_pkg in pkgutil.iter_modules([plugins_dir]):
            if not is_pkg:
                try:  
                    # Simple import without trying to reload
                    module_name = f"plugins.{name}"
                    module = importlib.import_module(module_name)
                    
                    click.echo(click.style(f"Loaded plugin module: {name}", fg="green"))
                    # Add more detailed debugging for version_command
                    if name == "version_command":
                        click.echo(f"Loaded version_command module: {module}")
                        click.echo(f"Module contents: {dir(module)}")
                except Exception as e:
                    click.echo(click.style(f"Error loading plugin {name}: {str(e)}", fg="red"))
                    # Print more details for exceptions
                    import traceback
                    click.echo(traceback.format_exc())
    except Exception as e:
        click.echo(click.style(f"Error loading plugins: {str(e)}", fg="red"))
