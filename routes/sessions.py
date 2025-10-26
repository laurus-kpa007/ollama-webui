from flask import Blueprint, request, jsonify
from services.session_manager import SessionManager
from models import db

sessions_bp = Blueprint('sessions', __name__, url_prefix='/api/sessions')

def get_session_manager():
    """Get session manager instance"""
    from flask import current_app
    redis_client = getattr(current_app, 'redis_client', None)
    return SessionManager(redis_client)

@sessions_bp.route('/', methods=['GET'])
def list_sessions():
    """List all sessions for current user"""
    user_id = request.args.get('user_id')
    include_archived = request.args.get('archived', 'false').lower() == 'true'

    if not user_id:
        # Get default user from config
        from flask import current_app
        user_id = current_app.config_manager.get('sessions.default_user_id', 'default-user')

    manager = get_session_manager()

    # Ensure user exists
    user = manager.get_or_create_default_user(user_id)

    sessions = manager.list_user_sessions(user.id, include_archived)

    return jsonify({
        'sessions': [s.to_dict() for s in sessions]
    })

@sessions_bp.route('/', methods=['POST'])
def create_session():
    """Create a new session"""
    data = request.get_json()
    user_id = data.get('user_id')
    model_name = data.get('model_name')
    mode = data.get('mode', 'chat')
    title = data.get('title')

    if not user_id:
        from flask import current_app
        user_id = current_app.config_manager.get('sessions.default_user_id', 'default-user')

    manager = get_session_manager()

    # Ensure user exists
    user = manager.get_or_create_default_user(user_id)

    session = manager.create_session(user.id, model_name, mode, title)

    return jsonify({
        'session': session.to_dict()
    }), 201

@sessions_bp.route('/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session details with messages"""
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    manager = get_session_manager()
    session = manager.get_session(session_id)

    if not session:
        return jsonify({'error': 'Session not found'}), 404

    messages = manager.get_session_messages(session_id, limit, offset)

    result = session.to_dict()
    result['messages'] = [m.to_dict() for m in messages]
    result['metadata'] = session.session_metadata.to_dict() if session.session_metadata else None

    return jsonify(result)

@sessions_bp.route('/<session_id>', methods=['PATCH'])
def update_session(session_id):
    """Update session (rename, pin, archive)"""
    data = request.get_json()
    manager = get_session_manager()

    if 'title' in data:
        success = manager.rename_session(session_id, data['title'])
        if not success:
            return jsonify({'error': 'Session not found'}), 404

    if 'archived' in data:
        if data['archived']:
            success = manager.archive_session(session_id)
        else:
            success = manager.unarchive_session(session_id)

        if not success:
            return jsonify({'error': 'Session not found'}), 404

    if 'pinned' in data:
        success = manager.toggle_pin_session(session_id)
        if not success:
            return jsonify({'error': 'Session not found'}), 404

    return jsonify({'success': True})

@sessions_bp.route('/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a session"""
    manager = get_session_manager()
    success = manager.delete_session(session_id)

    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Session not found'}), 404

@sessions_bp.route('/<session_id>/messages', methods=['POST'])
def add_message(session_id):
    """Add a message to session"""
    data = request.get_json()
    role = data.get('role')
    content = data.get('content')
    image_url = data.get('image_url')
    tool_calls = data.get('tool_calls')
    agent_name = data.get('agent_name')
    tokens_used = data.get('tokens_used')

    if not role or not content:
        return jsonify({'error': 'Role and content are required'}), 400

    manager = get_session_manager()
    message = manager.add_message(
        session_id=session_id,
        role=role,
        content=content,
        image_url=image_url,
        tool_calls=tool_calls,
        agent_name=agent_name,
        tokens_used=tokens_used
    )

    return jsonify({
        'message': message.to_dict()
    }), 201

@sessions_bp.route('/search', methods=['GET'])
def search_sessions():
    """Search sessions"""
    user_id = request.args.get('user_id')
    query = request.args.get('q', '')

    if not user_id:
        from flask import current_app
        user_id = current_app.config_manager.get('sessions.default_user_id', 'default-user')

    manager = get_session_manager()

    # Ensure user exists
    user = manager.get_or_create_default_user(user_id)

    sessions = manager.search_sessions(user.id, query)

    return jsonify({
        'sessions': [s.to_dict() for s in sessions]
    })

@sessions_bp.route('/<session_id>/metadata', methods=['PATCH'])
def update_session_metadata(session_id):
    """Update session metadata"""
    data = request.get_json()
    manager = get_session_manager()

    # Extract metadata fields
    metadata_fields = {
        'temperature': data.get('temperature'),
        'max_tokens': data.get('max_tokens'),
        'system_prompt': data.get('system_prompt'),
        'enabled_plugins': data.get('enabled_plugins'),
        'enabled_tools': data.get('enabled_tools'),
        'enabled_agents': data.get('enabled_agents')
    }

    # Filter out None values
    metadata_fields = {k: v for k, v in metadata_fields.items() if v is not None}

    success = manager.update_session_metadata(session_id, **metadata_fields)

    if success:
        return jsonify({'success': True})
    return jsonify({'error': 'Session not found or metadata update failed'}), 404
