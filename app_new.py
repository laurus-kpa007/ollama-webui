import os
from flask import Flask
from flask_cors import CORS
from models import db
from utils.config_manager import ConfigManager
import redis

def create_app(config_file='config.json'):
    """Application factory pattern"""

    app = Flask(__name__)
    CORS(app)

    # Load configuration
    config_manager = ConfigManager(config_file)
    app.config_manager = config_manager

    # Flask configurations
    app.config['SQLALCHEMY_DATABASE_URI'] = config_manager.get('database.uri')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = config_manager.get('security.secret_key')
    app.config['MAX_CONTENT_LENGTH'] = config_manager.get('security.max_content_length')
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'static/uploads')

    # Initialize database
    db.init_app(app)

    # Initialize Redis (optional)
    redis_config = config_manager.get_section('redis')
    if redis_config.get('enabled', False):
        try:
            app.redis_client = redis.Redis(
                host=redis_config['host'],
                port=redis_config['port'],
                db=redis_config['db'],
                decode_responses=True
            )
            # Test connection
            app.redis_client.ping()
            print("✓ Redis connected successfully")
        except Exception as e:
            print(f"✗ Redis connection failed: {e}")
            print("  Continuing without Redis caching...")
            app.redis_client = None
    else:
        app.redis_client = None
        print("  Redis caching disabled in config")

    # Import and register legacy client classes
    from app_backup import OllamaClient, ComfyUIClient, QwenImageClient

    ollama_config = config_manager.get_section('ollama')
    app.ollama_client = OllamaClient(
        host=ollama_config['host'],
        port=ollama_config['port']
    )

    comfyui_config = config_manager.get_section('comfyui')
    app.comfyui_client = ComfyUIClient(
        host=comfyui_config['host'],
        port=comfyui_config['port']
    )

    app.qwen_image_client = QwenImageClient()

    # Register blueprints
    from routes.sessions import sessions_bp
    app.register_blueprint(sessions_bp)

    # Import and register legacy routes
    register_legacy_routes(app)

    # Create database tables
    with app.app_context():
        db.create_all()
        print("✓ Database tables created")

        # Create default user
        from services.session_manager import SessionManager
        manager = SessionManager()
        default_username = config_manager.get('sessions.default_user_id', 'default-user')
        user = manager.get_or_create_default_user(default_username)
        print(f"✓ Default user '{user.username}' ready")

    return app

def register_legacy_routes(app):
    """Register legacy routes from original app.py"""
    from flask import render_template, request, jsonify, Response, stream_with_context
    import json
    import base64
    from PIL import Image
    from datetime import datetime
    import os

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/models')
    def get_models():
        models_data = app.ollama_client.get_models()
        return jsonify(models_data)

    @app.route('/api/chat', methods=['POST'])
    def chat():
        data = request.get_json()
        messages = data.get('messages', [])
        model = data.get('model')
        stream = data.get('stream', False)
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens')
        session_id = data.get('session_id')  # New: support session tracking

        # Save user message to session if provided
        if session_id:
            from services.session_manager import SessionManager
            manager = SessionManager(app.redis_client)
            # Get last user message
            if messages and messages[-1]['role'] == 'user':
                manager.add_message(
                    session_id=session_id,
                    role='user',
                    content=messages[-1]['content']
                )

        if not stream:
            response = app.ollama_client.chat_completion(messages, model, False, temperature, max_tokens)
            if response and response.status_code == 200:
                ollama_response = response.json()
                assistant_content = ollama_response.get("message", {}).get("content", "")

                # Save assistant response to session
                if session_id:
                    from services.session_manager import SessionManager
                    manager = SessionManager(app.redis_client)
                    manager.add_message(
                        session_id=session_id,
                        role='assistant',
                        content=assistant_content
                    )

                openai_format = {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": assistant_content
                        },
                        "finish_reason": "stop"
                    }]
                }
                return jsonify(openai_format)
            else:
                return jsonify({"error": "Ollama API 호출 실패"}), 500
        else:
            def generate():
                full_content = ""
                response = app.ollama_client.chat_completion(messages, model, True, temperature, max_tokens)
                if response and response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if data.get('done', False):
                                    # Save complete message to session
                                    if session_id and full_content:
                                        from services.session_manager import SessionManager
                                        manager = SessionManager(app.redis_client)
                                        manager.add_message(
                                            session_id=session_id,
                                            role='assistant',
                                            content=full_content
                                        )
                                    yield f"data: {json.dumps({'choices': [{'delta': {'content': ''}, 'finish_reason': 'stop'}]})}\n\n"
                                    break
                                else:
                                    content = data.get('message', {}).get('content', '')
                                    if content:
                                        full_content += content
                                        yield f"data: {json.dumps({'choices': [{'delta': {'content': content}}]})}\n\n"
                            except json.JSONDecodeError:
                                continue
                else:
                    yield f"data: {json.dumps({'error': 'API 호출 실패'})}\n\n"

            return Response(stream_with_context(generate()),
                           content_type='text/event-stream',
                           headers={'Cache-Control': 'no-cache'})

    @app.route('/api/upload', methods=['POST'])
    def upload_file():
        if 'file' not in request.files:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename

            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            try:
                with Image.open(file_path) as img:
                    img.verify()

                return jsonify({
                    'success': True,
                    'filename': filename,
                    'url': f'/static/uploads/{filename}'
                })
            except Exception as e:
                os.remove(file_path)
                return jsonify({'error': '유효하지 않은 이미지 파일입니다.'}), 400

        return jsonify({'error': '허용되지 않는 파일 형식입니다.'}), 400

    @app.route('/api/analyze_image', methods=['POST'])
    def analyze_image():
        data = request.get_json()
        image_url = data.get('image_url')
        prompt = data.get('prompt', '이 이미지에 대해 설명해주세요.')
        model = data.get('model', 'llava')

        if not image_url:
            return jsonify({'error': '이미지 URL이 필요합니다.'}), 400

        try:
            if image_url.startswith('/static/uploads/'):
                file_path = os.path.join(os.getcwd(), image_url[1:])
                with open(file_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
            else:
                return jsonify({'error': '유효하지 않은 이미지 경로입니다.'}), 400

            response = app.ollama_client.process_image(image_data, prompt, model)
            if response and response.status_code == 200:
                ollama_response = response.json()
                openai_format = {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": ollama_response.get("response", "")
                        },
                        "finish_reason": "stop"
                    }]
                }
                return jsonify(openai_format)
            else:
                return jsonify({'error': '이미지 분석 실패'}), 500

        except Exception as e:
            return jsonify({'error': f'이미지 처리 중 오류: {str(e)}'}), 500

    @app.route('/api/image_models')
    def get_image_models():
        """이미지 생성 모델 목록 조회"""
        try:
            image_models = []

            # Qwen-Image 직접 구현 모델 추가
            qwen_available = app.qwen_image_client.is_available()
            image_models.append({
                "model_name": "qwen-direct",
                "title": "🎨 Qwen-Image (직접 구현)",
                "type": "direct",
                "available": qwen_available,
                "description": "Diffusers를 통한 직접 구현"
            })

            # ComfyUI 연결 확인
            comfyui_connected = app.comfyui_client.check_connection()

            if comfyui_connected:
                # ComfyUI 기반 모델들
                available_models = app.comfyui_client.get_available_models()
                if available_models:
                    for model in available_models:
                        image_models.append({
                            "model_name": model,
                            "title": model.replace('.safetensors', '').replace('.ckpt', '').replace('_', ' ').title(),
                            "type": "comfyui",
                            "available": True,
                            "description": "ComfyUI SDXL 모델"
                        })

            return jsonify({
                "data": image_models,
                "comfyui_connected": comfyui_connected,
                "qwen_direct_available": qwen_available
            })

        except Exception as e:
            return jsonify({
                "data": [{
                    "model_name": "qwen-direct",
                    "title": "🎨 Qwen-Image (직접 구현)",
                    "type": "direct",
                    "available": app.qwen_image_client.is_available(),
                    "description": "Diffusers를 통한 직접 구현"
                }],
                "error": f"오류: {str(e)}",
                "comfyui_connected": False,
                "qwen_direct_available": app.qwen_image_client.is_available()
            })

    @app.route('/api/generate_image', methods=['POST'])
    def generate_image():
        # Delegate to original implementation in app_backup
        # This is simplified - full implementation kept in app_backup.py
        return jsonify({'error': 'Image generation route - see app_backup.py for full implementation'}), 501

    def allowed_file(filename):
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    def secure_filename(filename):
        import re
        filename = re.sub(r'[^\w\s.-]', '', filename).strip()
        return re.sub(r'[-\s]+', '-', filename)

if __name__ == '__main__':
    app = create_app()

    host = app.config_manager.get('app.host', '0.0.0.0')
    port = app.config_manager.get('app.port', 5000)
    debug = app.config_manager.get('app.debug', False)

    print(f"\n{'='*50}")
    print(f"  Ollama WebUI v2.0")
    print(f"  Running on http://{host}:{port}")
    print(f"{'='*50}\n")

    app.run(host=host, port=port, debug=debug)
