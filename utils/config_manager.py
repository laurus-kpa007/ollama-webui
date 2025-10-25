import json
import os
from typing import Dict, Any
from pathlib import Path

class ConfigManager:
    """Centralized configuration management"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            # Create default config
            self.config = self._default_config()
            self.save_config()

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value

        Args:
            key: Configuration key (supports dot notation, e.g., 'database.host')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        self.save_config()

    def get_section(self, section: str) -> Dict:
        """Get entire configuration section

        Args:
            section: Section name

        Returns:
            Dictionary of section configuration
        """
        return self.config.get(section, {})

    def update_section(self, section: str, values: Dict):
        """Update configuration section

        Args:
            section: Section name
            values: Dictionary of values to update
        """
        if section not in self.config:
            self.config[section] = {}

        self.config[section].update(values)
        self.save_config()

    def _default_config(self) -> Dict:
        """Generate default configuration"""
        return {
            'app': {
                'name': 'Ollama WebUI',
                'version': '2.0.0',
                'debug': False,
                'host': '0.0.0.0',
                'port': 5000
            },
            'database': {
                'uri': 'sqlite:///app.db',
                'pool_size': 10,
                'echo': False
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'enabled': False  # Optional - disable if Redis not available
            },
            'ollama': {
                'host': 'localhost',
                'port': 11434,
                'default_model': 'llama2'
            },
            'comfyui': {
                'host': 'localhost',
                'port': 8188,
                'enabled': True
            },
            'sessions': {
                'max_per_user': 100,
                'auto_archive_days': 30,
                'default_user_id': 'default-user'  # For single-user mode
            },
            'plugins': {
                'directory': 'plugins',
                'enabled': []
            },
            'security': {
                'secret_key': os.urandom(24).hex(),
                'max_content_length': 16 * 1024 * 1024
            },
            'autogen': {
                'enabled': False,
                'default_agents': ['researcher', 'coder', 'creative']
            },
            'mcp': {
                'enabled': False,
                'servers': []
            }
        }
