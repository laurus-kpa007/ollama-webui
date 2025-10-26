"""
Autogen Routes - API endpoints for multi-agent system (Updated for AutoGen 0.7.5)
"""
from flask import Blueprint, request, jsonify, current_app
from services.autogen_service import get_autogen_service, initialize_autogen_service
import asyncio

autogen_bp = Blueprint('autogen', __name__, url_prefix='/api/autogen')


def run_async(coro):
    """Helper to run async functions in Flask routes"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@autogen_bp.route('/agents', methods=['GET'])
def list_agents():
    """List available agents"""
    try:
        service = get_autogen_service()

        # Initialize agents if not already done
        if not service.agents:
            run_async(service.create_agents())

        agents = service.get_available_agents()

        return jsonify({
            'agents': agents,
            'count': len(agents)
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@autogen_bp.route('/task/sequential', methods=['POST'])
def sequential_task():
    """Execute a sequential task across multiple agents"""
    data = request.get_json()
    task = data.get('task')
    agents = data.get('agents', ['researcher', 'coder', 'critic'])
    temperature = data.get('temperature', 0.7)

    if not task:
        return jsonify({
            'error': 'Task description is required'
        }), 400

    try:
        service = get_autogen_service()

        # Recreate agents with custom temperature if needed
        if temperature != 0.7:
            run_async(service.create_agents(temperature))

        # Run async task
        result = run_async(service.sequential_task(task, agents))

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'task': task,
            'agents': agents
        }), 500


@autogen_bp.route('/task/group', methods=['POST'])
def group_task():
    """Execute a group collaboration task"""
    data = request.get_json()
    task = data.get('task')
    agents = data.get('agents', ['researcher', 'coder', 'creative', 'critic'])
    max_round = data.get('max_round', 12)
    temperature = data.get('temperature', 0.7)

    if not task:
        return jsonify({
            'error': 'Task description is required'
        }), 400

    try:
        service = get_autogen_service()

        # Recreate agents with custom temperature if needed
        if temperature != 0.7:
            run_async(service.create_agents(temperature))

        # Run async task
        result = run_async(service.group_task(task, agents, max_round))

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'task': task,
            'agents': agents
        }), 500


@autogen_bp.route('/image/enhance', methods=['POST'])
def enhance_image_prompt():
    """Use multi-agent workflow to enhance image prompt"""
    data = request.get_json()
    user_prompt = data.get('prompt')

    if not user_prompt:
        return jsonify({
            'error': 'Prompt is required'
        }), 400

    try:
        service = get_autogen_service()

        # Run async workflow
        result = run_async(service.image_generation_workflow(user_prompt))

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'error': str(e),
            'prompt': user_prompt
        }), 500


@autogen_bp.route('/session/<session_id>/agents', methods=['GET', 'PATCH'])
def manage_session_agents(session_id):
    """Get or update enabled agents for a session"""
    from services.session_manager import SessionManager

    manager = SessionManager(current_app.redis_client if hasattr(current_app, 'redis_client') else None)

    if request.method == 'GET':
        # Get enabled agents
        session = manager.get_session(session_id)
        if not session or not session.metadata:
            return jsonify({'error': 'Session not found'}), 404

        return jsonify({
            'enabled_agents': session.metadata.enabled_agents or []
        })

    elif request.method == 'PATCH':
        # Update enabled agents
        data = request.get_json()
        enabled_agents = data.get('enabled_agents', [])

        success = manager.update_session_metadata(
            session_id,
            enabled_agents=enabled_agents
        )

        if success:
            return jsonify({
                'success': True,
                'enabled_agents': enabled_agents
            })
        else:
            return jsonify({
                'error': 'Failed to update session agents'
            }), 500


@autogen_bp.route('/workflows', methods=['GET'])
def list_workflows():
    """List available agent workflows"""
    workflows = [
        {
            'id': 'sequential',
            'name': 'Sequential Workflow',
            'description': 'Agents work one after another in round-robin fashion',
            'recommended_agents': ['researcher', 'coder', 'critic'],
            'use_cases': ['Research and analysis', 'Code generation with review', 'Content creation pipeline']
        },
        {
            'id': 'group',
            'name': 'Group Chat',
            'description': 'Agents collaborate with dynamic speaker selection',
            'recommended_agents': ['researcher', 'coder', 'creative', 'critic'],
            'use_cases': ['Brainstorming', 'Complex problem solving', 'Multi-perspective analysis']
        },
        {
            'id': 'image_enhancement',
            'name': 'Image Prompt Enhancement',
            'description': 'Specialized workflow for enhancing image prompts',
            'recommended_agents': ['creative', 'critic', 'image_specialist'],
            'use_cases': ['Image generation', 'Prompt refinement', 'Creative direction']
        }
    ]

    return jsonify({
        'workflows': workflows
    })


@autogen_bp.route('/config', methods=['GET', 'POST'])
def manage_config():
    """Get or update AutoGen configuration"""
    if request.method == 'GET':
        config = {
            'ollama_url': current_app.config_manager.get('ollama.host', 'localhost'),
            'ollama_port': current_app.config_manager.get('ollama.port', 11434),
            'default_temperature': 0.7,
            'default_max_round': 12,
            'enabled': current_app.config_manager.get('autogen.enabled', False),
            'version': '0.7.5'
        }
        return jsonify(config)

    elif request.method == 'POST':
        data = request.get_json()

        if 'enabled' in data:
            current_app.config_manager.set('autogen.enabled', data['enabled'])

        return jsonify({'success': True})


@autogen_bp.route('/test', methods=['POST'])
def test_agents():
    """Test agent system with sample task"""
    try:
        service = get_autogen_service()

        # Initialize agents if needed
        if not service.agents:
            run_async(service.create_agents())

        # Simple test task
        test_task = "What are the benefits of using Python for web development? Keep the answer brief."

        result = run_async(service.sequential_task(
            test_task,
            ['researcher', 'critic']
        ))

        return jsonify({
            'test': 'Sequential task test',
            'task': test_task,
            'success': True,
            'result': result
        })

    except Exception as e:
        return jsonify({
            'test': 'Sequential task test',
            'success': False,
            'error': str(e)
        }), 500


@autogen_bp.route('/clear', methods=['POST'])
def clear_conversation():
    """Clear conversation history"""
    try:
        service = get_autogen_service()
        service.clear_conversation()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@autogen_bp.route('/initialize', methods=['POST'])
def initialize():
    """Initialize the AutoGen service and create agents"""
    try:
        service = run_async(initialize_autogen_service())

        return jsonify({
            'success': True,
            'agents': service.get_available_agents(),
            'version': '0.7.5'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
