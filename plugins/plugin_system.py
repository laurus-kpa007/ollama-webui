"""
Plugin System - Base classes and plugin manager
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import importlib
import pkgutil
import inspect
from pathlib import Path

class PluginBase(ABC):
    """Base class for all plugins"""

    # Plugin metadata
    name: str = "Unknown Plugin"
    version: str = "0.0.0"
    description: str = ""
    author: str = ""

    def __init__(self, app_context: Any = None):
        """Initialize plugin with application context

        Args:
            app_context: Application context (Flask app, config, etc.)
        """
        self.app_context = app_context
        self.enabled = False

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin

        Returns:
            True if initialization successful
        """
        pass

    @abstractmethod
    def cleanup(self):
        """Cleanup resources when plugin is disabled"""
        pass

    def get_routes(self) -> List[Dict]:
        """Return Flask routes to register

        Returns:
            List of route dictionaries
        """
        return []

    def get_config(self) -> Dict:
        """Return plugin configuration schema

        Returns:
            Dictionary describing configuration options
        """
        return {}

    def on_message(self, message: Dict) -> Optional[Dict]:
        """Hook called when a chat message is sent

        Args:
            message: Message dictionary

        Returns:
            Modified message or None
        """
        return None

    def on_response(self, response: Dict) -> Optional[Dict]:
        """Hook called when a response is received

        Args:
            response: Response dictionary

        Returns:
            Modified response or None
        """
        return None


class PluginManager:
    """Manages plugin discovery, loading, and lifecycle"""

    def __init__(self, plugin_directory: str = "plugins"):
        self.plugin_directory = Path(plugin_directory)
        self.plugins: Dict[str, PluginBase] = {}
        self.enabled_plugins: set = set()

        # Create plugin directory if it doesn't exist
        self.plugin_directory.mkdir(exist_ok=True)

    def discover_plugins(self) -> List[str]:
        """Discover available plugins

        Returns:
            List of discovered plugin names
        """
        discovered = []

        # Add plugin directory to path
        import sys
        if str(self.plugin_directory) not in sys.path:
            sys.path.insert(0, str(self.plugin_directory))

        # Iterate through modules in plugin directory
        for finder, name, ispkg in pkgutil.iter_modules([str(self.plugin_directory)]):
            if name.startswith('_') or name == 'plugin_system':
                continue

            try:
                module = importlib.import_module(name)

                # Find plugin classes
                for item_name in dir(module):
                    item = getattr(module, item_name)

                    # Check if it's a plugin class
                    if (inspect.isclass(item) and
                        issubclass(item, PluginBase) and
                        item is not PluginBase):

                        discovered.append(name)
                        break

            except Exception as e:
                print(f"Error discovering plugin {name}: {e}")

        return discovered

    def load_plugin(self, plugin_name: str, app_context: Any = None) -> bool:
        """Load a plugin

        Args:
            plugin_name: Name of the plugin module
            app_context: Application context to pass to plugin

        Returns:
            True if loaded successfully
        """
        try:
            module = importlib.import_module(plugin_name)

            # Find the plugin class
            plugin_class = None
            for item_name in dir(module):
                item = getattr(module, item_name)
                if (inspect.isclass(item) and
                    issubclass(item, PluginBase) and
                    item is not PluginBase):
                    plugin_class = item
                    break

            if not plugin_class:
                raise ValueError(f"No plugin class found in {plugin_name}")

            # Instantiate plugin
            plugin_instance = plugin_class(app_context)
            self.plugins[plugin_name] = plugin_instance

            print(f"✓ Loaded plugin: {plugin_instance.name}")
            return True

        except Exception as e:
            print(f"✗ Error loading plugin {plugin_name}: {e}")
            return False

    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if enabled successfully
        """
        if plugin_name not in self.plugins:
            if not self.load_plugin(plugin_name):
                return False

        plugin = self.plugins[plugin_name]

        try:
            if plugin.initialize():
                plugin.enabled = True
                self.enabled_plugins.add(plugin_name)
                print(f"✓ Enabled plugin: {plugin.name}")
                return True
        except Exception as e:
            print(f"✗ Error enabling plugin {plugin_name}: {e}")

        return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if disabled successfully
        """
        if plugin_name not in self.plugins:
            return False

        plugin = self.plugins[plugin_name]

        try:
            plugin.cleanup()
            plugin.enabled = False
            self.enabled_plugins.discard(plugin_name)
            print(f"✓ Disabled plugin: {plugin.name}")
            return True
        except Exception as e:
            print(f"✗ Error disabling plugin {plugin_name}: {e}")
            return False

    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """Get a plugin instance

        Args:
            plugin_name: Name of the plugin

        Returns:
            Plugin instance or None
        """
        return self.plugins.get(plugin_name)

    def list_plugins(self) -> List[Dict]:
        """List all plugins

        Returns:
            List of plugin information dictionaries
        """
        return [
            {
                'name': name,
                'display_name': plugin.name,
                'version': plugin.version,
                'description': plugin.description,
                'author': plugin.author,
                'enabled': plugin.enabled
            }
            for name, plugin in self.plugins.items()
        ]

    def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Call a hook on all enabled plugins

        Args:
            hook_name: Name of the hook method
            *args, **kwargs: Arguments to pass to hook

        Returns:
            List of results from all plugins
        """
        results = []

        for plugin_name in self.enabled_plugins:
            plugin = self.plugins[plugin_name]

            if hasattr(plugin, hook_name):
                try:
                    result = getattr(plugin, hook_name)(*args, **kwargs)
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    print(f"Error calling {hook_name} on {plugin_name}: {e}")

        return results
