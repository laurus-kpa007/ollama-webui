"""
Example Plugin - Demonstrates plugin capabilities
"""
from plugin_system import PluginBase
from typing import Dict, Optional, List

class ExamplePlugin(PluginBase):
    """Example plugin showing various features"""

    name = "Example Plugin"
    version = "1.0.0"
    description = "Demonstrates plugin system capabilities"
    author = "Ollama WebUI"

    def __init__(self, app_context=None):
        super().__init__(app_context)
        self.message_count = 0

    def initialize(self) -> bool:
        """Initialize the plugin"""
        print(f"{self.name} initialized")
        return True

    def cleanup(self):
        """Cleanup resources"""
        print(f"{self.name} cleaned up. Processed {self.message_count} messages")

    def get_routes(self) -> List[Dict]:
        """Register Flask routes"""
        return [
            {
                'rule': '/api/plugins/example/stats',
                'endpoint': 'example_stats',
                'view_func': self.get_stats,
                'methods': ['GET']
            }
        ]

    def get_config(self) -> Dict:
        """Configuration schema"""
        return {
            'enabled': {
                'type': 'boolean',
                'default': True,
                'description': 'Enable this plugin'
            },
            'message_prefix': {
                'type': 'string',
                'default': '[Plugin]',
                'description': 'Prefix to add to messages'
            }
        }

    def on_message(self, message: Dict) -> Optional[Dict]:
        """Process chat messages"""
        self.message_count += 1

        # Example: Add metadata to message
        if message.get('role') == 'user':
            message['processed_by'] = self.name

        return message

    def on_response(self, response: Dict) -> Optional[Dict]:
        """Process responses"""
        # Example: Add footer to responses
        if 'content' in response:
            response['plugin_processed'] = True

        return response

    def get_stats(self):
        """Flask route handler"""
        from flask import jsonify

        return jsonify({
            'plugin': self.name,
            'message_count': self.message_count,
            'enabled': self.enabled
        })
