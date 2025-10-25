"""
MCP Routes - API endpoints for MCP tool management
"""
from flask import Blueprint, request, jsonify, current_app
from services.mcp_client import get_mcp_client
import asyncio
import os

mcp_bp = Blueprint('mcp', __name__, url_prefix='/api/mcp')

def run_async(coro):
    """Helper to run async functions in Flask routes"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@mcp_bp.route('/connect', methods=['POST'])
def connect():
    """Connect to an MCP server"""
    data = request.get_json()
    server_path = data.get('server_path', 'services/mcp_server.py')

    # Make path absolute
    if not os.path.isabs(server_path):
        server_path = os.path.join(os.getcwd(), server_path)

    client = get_mcp_client()

    try:
        success = run_async(client.connect_to_server(server_path))

        if success:
            tools = run_async(client.get_available_tools())
            resources = run_async(client.get_available_resources())

            return jsonify({
                'success': True,
                'server_info': client.server_info,
                'tools': tools,
                'resources': resources
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to connect to MCP server'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mcp_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from MCP server"""
    client = get_mcp_client()

    try:
        run_async(client.disconnect())
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mcp_bp.route('/status', methods=['GET'])
def status():
    """Get MCP connection status"""
    client = get_mcp_client()

    return jsonify({
        'connected': client.is_connected(),
        'server_info': client.server_info if client.is_connected() else None
    })

@mcp_bp.route('/tools', methods=['GET'])
def list_tools():
    """List available tools from MCP server"""
    client = get_mcp_client()

    if not client.is_connected():
        return jsonify({
            'error': 'Not connected to MCP server'
        }), 400

    try:
        tools = run_async(client.get_available_tools())
        return jsonify({
            'tools': tools,
            'count': len(tools)
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@mcp_bp.route('/tools/<tool_name>', methods=['GET'])
def get_tool_info(tool_name):
    """Get information about a specific tool"""
    client = get_mcp_client()

    if not client.is_connected():
        return jsonify({
            'error': 'Not connected to MCP server'
        }), 400

    try:
        tool_info = run_async(client.get_tool_info(tool_name))

        if tool_info:
            return jsonify(tool_info)
        else:
            return jsonify({
                'error': f'Tool "{tool_name}" not found'
            }), 404

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@mcp_bp.route('/tools/<tool_name>/call', methods=['POST'])
def call_tool(tool_name):
    """Call a tool on the MCP server"""
    client = get_mcp_client()

    if not client.is_connected():
        return jsonify({
            'error': 'Not connected to MCP server'
        }), 400

    data = request.get_json()
    arguments = data.get('arguments', {})

    try:
        result = run_async(client.call_tool(tool_name, arguments))

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mcp_bp.route('/resources', methods=['GET'])
def list_resources():
    """List available resources from MCP server"""
    client = get_mcp_client()

    if not client.is_connected():
        return jsonify({
            'error': 'Not connected to MCP server'
        }), 400

    try:
        resources = run_async(client.get_available_resources())
        return jsonify({
            'resources': resources,
            'count': len(resources)
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@mcp_bp.route('/resources/<path:uri>', methods=['GET'])
def get_resource(uri):
    """Get a resource from the MCP server"""
    client = get_mcp_client()

    if not client.is_connected():
        return jsonify({
            'error': 'Not connected to MCP server'
        }), 400

    try:
        content = run_async(client.get_resource(uri))

        if content is not None:
            return jsonify({
                'uri': uri,
                'content': content
            })
        else:
            return jsonify({
                'error': f'Resource "{uri}" not found'
            }), 404

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@mcp_bp.route('/session/<session_id>/tools', methods=['GET', 'PATCH'])
def manage_session_tools(session_id):
    """Get or update enabled tools for a session"""
    from services.session_manager import SessionManager

    manager = SessionManager(current_app.redis_client if hasattr(current_app, 'redis_client') else None)

    if request.method == 'GET':
        # Get enabled tools
        session = manager.get_session(session_id)
        if not session or not session.metadata:
            return jsonify({'error': 'Session not found'}), 404

        return jsonify({
            'enabled_tools': session.metadata.enabled_tools or []
        })

    elif request.method == 'PATCH':
        # Update enabled tools
        data = request.get_json()
        enabled_tools = data.get('enabled_tools', [])

        success = manager.update_session_metadata(
            session_id,
            enabled_tools=enabled_tools
        )

        if success:
            return jsonify({
                'success': True,
                'enabled_tools': enabled_tools
            })
        else:
            return jsonify({
                'error': 'Failed to update session tools'
            }), 500

@mcp_bp.route('/test', methods=['POST'])
def test_tools():
    """Test MCP tools with sample data"""
    client = get_mcp_client()

    if not client.is_connected():
        # Try to connect first
        try:
            server_path = os.path.join(os.getcwd(), 'services/mcp_server.py')
            success = run_async(client.connect_to_server(server_path))
            if not success:
                return jsonify({
                    'error': 'Failed to connect to MCP server'
                }), 500
        except Exception as e:
            return jsonify({
                'error': f'Failed to connect: {str(e)}'
            }), 500

    # Run test cases
    test_results = []

    test_cases = [
        {
            'name': 'add_numbers',
            'arguments': {'a': 5, 'b': 3},
            'expected': 8
        },
        {
            'name': 'count_words',
            'arguments': {'text': 'Hello world from MCP'},
            'expected': 4
        },
        {
            'name': 'get_current_date',
            'arguments': {},
            'expected': None  # Just check it works
        }
    ]

    for test in test_cases:
        try:
            result = run_async(client.call_tool(test['name'], test['arguments']))
            test_results.append({
                'tool': test['name'],
                'success': result.get('success', False),
                'result': result.get('result'),
                'expected': test['expected']
            })
        except Exception as e:
            test_results.append({
                'tool': test['name'],
                'success': False,
                'error': str(e)
            })

    return jsonify({
        'test_results': test_results,
        'total_tests': len(test_cases),
        'passed': sum(1 for t in test_results if t.get('success', False))
    })
