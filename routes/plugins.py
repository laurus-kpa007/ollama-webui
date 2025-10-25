"""
Plugin Routes - API endpoints for plugin management
"""
from flask import Blueprint, request, jsonify, current_app

plugins_bp = Blueprint('plugins', __name__, url_prefix='/api/plugins')

@plugins_bp.route('/', methods=['GET'])
def list_plugins():
    """List all available plugins"""
    try:
        if not hasattr(current_app, 'plugin_manager'):
            return jsonify({'plugins': [], 'error': 'Plugin manager not initialized'})

        plugins = current_app.plugin_manager.list_plugins()
        return jsonify({
            'plugins': plugins,
            'count': len(plugins)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@plugins_bp.route('/discover', methods=['POST'])
def discover_plugins():
    """Discover available plugins"""
    try:
        if not hasattr(current_app, 'plugin_manager'):
            return jsonify({'error': 'Plugin manager not initialized'}), 500

        discovered = current_app.plugin_manager.discover_plugins()
        return jsonify({
            'plugins': discovered,
            'count': len(discovered)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@plugins_bp.route('/<plugin_name>/enable', methods=['POST'])
def enable_plugin(plugin_name):
    """Enable a plugin"""
    try:
        if not hasattr(current_app, 'plugin_manager'):
            return jsonify({'error': 'Plugin manager not initialized'}), 500

        success = current_app.plugin_manager.enable_plugin(plugin_name)

        if success:
            return jsonify({'success': True, 'plugin': plugin_name})
        else:
            return jsonify({'success': False, 'error': 'Failed to enable plugin'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@plugins_bp.route('/<plugin_name>/disable', methods=['POST'])
def disable_plugin(plugin_name):
    """Disable a plugin"""
    try:
        if not hasattr(current_app, 'plugin_manager'):
            return jsonify({'error': 'Plugin manager not initialized'}), 500

        success = current_app.plugin_manager.disable_plugin(plugin_name)

        if success:
            return jsonify({'success': True, 'plugin': plugin_name})
        else:
            return jsonify({'success': False, 'error': 'Failed to disable plugin'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@plugins_bp.route('/<plugin_name>', methods=['GET'])
def get_plugin_info(plugin_name):
    """Get information about a specific plugin"""
    try:
        if not hasattr(current_app, 'plugin_manager'):
            return jsonify({'error': 'Plugin manager not initialized'}), 500

        plugin = current_app.plugin_manager.get_plugin(plugin_name)

        if not plugin:
            return jsonify({'error': 'Plugin not found'}), 404

        return jsonify({
            'name': plugin_name,
            'display_name': plugin.name,
            'version': plugin.version,
            'description': plugin.description,
            'author': plugin.author,
            'enabled': plugin.enabled,
            'config_schema': plugin.get_config()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
