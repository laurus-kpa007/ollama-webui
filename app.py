import os
import json
import requests
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from PIL import Image
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

logging.basicConfig(level=logging.DEBUG)

class OllamaClient:
    def __init__(self, host='localhost', port=11434):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        
    def get_models(self):
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = []
                for model in data.get('models', []):
                    models.append({
                        "id": model['name'],
                        "object": "model",
                        "created": 0,
                        "owned_by": "ollama"
                    })
                return {"data": models}
            return {"data": [], "error": "Ollama 서버에 연결할 수 없습니다."}
        except requests.exceptions.ConnectionError:
            return {"data": [], "error": "Ollama가 실행되지 않거나 포트가 다릅니다."}
        except Exception as e:
            return {"data": [], "error": f"오류: {str(e)}"}
    
    def chat_completion(self, messages, model=None, stream=False, temperature=0.7, max_tokens=None):
        url = f"{self.base_url}/api/chat"
        
        data = {
            "model": model or "llama2",
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        
        if max_tokens:
            data["options"]["num_predict"] = max_tokens
            
        try:
            response = requests.post(url, json=data, stream=stream)
            return response
        except Exception as e:
            return None

    def process_image(self, image_data, prompt, model=None):
        url = f"{self.base_url}/api/generate"
        
        data = {
            "model": model or "llava",
            "prompt": prompt,
            "images": [image_data],
            "stream": False
        }
        
        try:
            response = requests.post(url, json=data)
            return response
        except Exception as e:
            return None

class StableDiffusionClient:
    def __init__(self, host='localhost', port=7860):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        
    def check_connection(self):
        try:
            response = requests.get(f"{self.base_url}/sdapi/v1/sd-models")
            return response.status_code == 200
        except:
            return False
    
    def get_models(self):
        try:
            response = requests.get(f"{self.base_url}/sdapi/v1/sd-models")
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []
    
    def txt2img(self, prompt, negative_prompt="", width=512, height=512, steps=20, cfg_scale=7, sampler="Euler", model=None):
        url = f"{self.base_url}/sdapi/v1/txt2img"
        
        data = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "sampler_name": sampler,
            "batch_size": 1,
            "n_iter": 1,
            "seed": -1,
            "restore_faces": False,
            "tiling": False
        }
        
        if model:
            # 모델 변경
            model_data = {"sd_model_checkpoint": model}
            requests.post(f"{self.base_url}/sdapi/v1/options", json=model_data)
        
        try:
            response = requests.post(url, json=data)
            return response
        except Exception as e:
            return None
    
    def img2img(self, init_images, prompt, negative_prompt="", denoising_strength=0.7, width=512, height=512, steps=20, cfg_scale=7, sampler="Euler"):
        url = f"{self.base_url}/sdapi/v1/img2img"
        
        data = {
            "init_images": init_images,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "denoising_strength": denoising_strength,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "sampler_name": sampler,
            "batch_size": 1,
            "n_iter": 1,
            "seed": -1
        }
        
        try:
            response = requests.post(url, json=data)
            return response
        except Exception as e:
            return None

ollama_client = OllamaClient(
    host=os.getenv('OLLAMA_HOST', 'localhost'),
    port=int(os.getenv('OLLAMA_PORT', 11434))
)

sd_client = StableDiffusionClient(
    host=os.getenv('SD_HOST', 'localhost'),
    port=int(os.getenv('SD_PORT', 7860))
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/models')
def get_models():
    models_data = ollama_client.get_models()
    return jsonify(models_data)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    messages = data.get('messages', [])
    model = data.get('model')
    stream = data.get('stream', False)
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens')
    
    if not stream:
        response = ollama_client.chat_completion(messages, model, False, temperature, max_tokens)
        if response and response.status_code == 200:
            ollama_response = response.json()
            # Ollama 응답을 OpenAI 형식으로 변환
            openai_format = {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": ollama_response.get("message", {}).get("content", "")
                    },
                    "finish_reason": "stop"
                }]
            }
            return jsonify(openai_format)
        else:
            return jsonify({"error": "Ollama API 호출 실패"}), 500
    else:
        def generate():
            response = ollama_client.chat_completion(messages, model, True, temperature, max_tokens)
            if response and response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if data.get('done', False):
                                yield f"data: {json.dumps({'choices': [{'delta': {'content': ''}, 'finish_reason': 'stop'}]})}\n\n"
                                break
                            else:
                                content = data.get('message', {}).get('content', '')
                                if content:
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
        
        response = ollama_client.process_image(image_data, prompt, model)
        if response and response.status_code == 200:
            ollama_response = response.json()
            # Ollama 응답을 OpenAI 형식으로 변환
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

@app.route('/api/sd_models')
def get_sd_models():
    try:
        if not sd_client.check_connection():
            return jsonify({"data": [], "error": "Stable Diffusion 서버에 연결할 수 없습니다."})
        
        models = sd_client.get_models()
        return jsonify({"data": models, "connected": True})
    except Exception as e:
        return jsonify({"data": [], "error": f"오류: {str(e)}", "connected": False})

@app.route('/api/generate_image', methods=['POST'])
def generate_image():
    data = request.get_json()
    prompt = data.get('prompt', '')
    negative_prompt = data.get('negative_prompt', '')
    width = int(data.get('width', 512))
    height = int(data.get('height', 512))
    steps = int(data.get('steps', 20))
    cfg_scale = float(data.get('cfg_scale', 7))
    sampler = data.get('sampler', 'Euler')
    model = data.get('model')
    
    if not prompt:
        return jsonify({'error': '프롬프트가 필요합니다.'}), 400
    
    try:
        response = sd_client.txt2img(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            cfg_scale=cfg_scale,
            sampler=sampler,
            model=model
        )
        
        if response and response.status_code == 200:
            result = response.json()
            if result.get('images') and len(result['images']) > 0:
                # 생성된 이미지를 파일로 저장
                image_data = result['images'][0]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"generated_{timestamp}.png"
                
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # base64 이미지를 파일로 저장
                import base64
                with open(file_path, 'wb') as f:
                    f.write(base64.b64decode(image_data))
                
                return jsonify({
                    'success': True,
                    'image_url': f'/static/uploads/{filename}',
                    'info': result.get('info', {})
                })
            else:
                return jsonify({'error': '이미지 생성에 실패했습니다.'}), 500
        else:
            return jsonify({'error': 'Stable Diffusion API 호출 실패'}), 500
            
    except Exception as e:
        return jsonify({'error': f'이미지 생성 중 오류: {str(e)}'}), 500

@app.route('/api/img2img', methods=['POST'])
def img2img():
    data = request.get_json()
    init_image_url = data.get('init_image_url')
    prompt = data.get('prompt', '')
    negative_prompt = data.get('negative_prompt', '')
    denoising_strength = float(data.get('denoising_strength', 0.7))
    width = int(data.get('width', 512))
    height = int(data.get('height', 512))
    steps = int(data.get('steps', 20))
    cfg_scale = float(data.get('cfg_scale', 7))
    sampler = data.get('sampler', 'Euler')
    
    if not prompt or not init_image_url:
        return jsonify({'error': '프롬프트와 초기 이미지가 필요합니다.'}), 400
    
    try:
        # 초기 이미지 로드
        if init_image_url.startswith('/static/uploads/'):
            file_path = os.path.join(os.getcwd(), init_image_url[1:])
            with open(file_path, 'rb') as f:
                init_image_b64 = base64.b64encode(f.read()).decode('utf-8')
        else:
            return jsonify({'error': '유효하지 않은 이미지 경로입니다.'}), 400
        
        response = sd_client.img2img(
            init_images=[init_image_b64],
            prompt=prompt,
            negative_prompt=negative_prompt,
            denoising_strength=denoising_strength,
            width=width,
            height=height,
            steps=steps,
            cfg_scale=cfg_scale,
            sampler=sampler
        )
        
        if response and response.status_code == 200:
            result = response.json()
            if result.get('images') and len(result['images']) > 0:
                # 생성된 이미지를 파일로 저장
                image_data = result['images'][0]
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"img2img_{timestamp}.png"
                
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # base64 이미지를 파일로 저장
                with open(file_path, 'wb') as f:
                    f.write(base64.b64decode(image_data))
                
                return jsonify({
                    'success': True,
                    'image_url': f'/static/uploads/{filename}',
                    'info': result.get('info', {})
                })
            else:
                return jsonify({'error': '이미지 변환에 실패했습니다.'}), 500
        else:
            return jsonify({'error': 'Stable Diffusion API 호출 실패'}), 500
            
    except Exception as e:
        return jsonify({'error': f'이미지 변환 중 오류: {str(e)}'}), 500

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def secure_filename(filename):
    import re
    filename = re.sub(r'[^\w\s.-]', '', filename).strip()
    return re.sub(r'[-\s]+', '-', filename)

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )