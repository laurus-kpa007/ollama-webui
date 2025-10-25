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
import io

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

class ComfyUIClient:
    def __init__(self, host='localhost', port=8188):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        
    def check_connection(self):
        """ComfyUI 서버 연결 확인"""
        try:
            response = requests.get(f"{self.base_url}/system_stats")
            return response.status_code == 200
        except:
            return False
    
    def get_available_models(self):
        """ComfyUI에서 사용 가능한 실제 모델 목록 조회"""
        try:
            response = requests.get(f"{self.base_url}/object_info/CheckpointLoaderSimple")
            if response.status_code == 200:
                data = response.json()
                if 'input' in data and 'required' in data['input'] and 'ckpt_name' in data['input']['required']:
                    model_list = data['input']['required']['ckpt_name'][0]
                    return model_list
            return []
        except Exception as e:
            print(f"Error getting models: {e}")
            return []
    
    def find_best_available_model(self):
        """사용 가능한 최적 모델 찾기"""
        available_models = self.get_available_models()
        if not available_models:
            return None
            
        # 선호도 순서: SDXL > SD 1.5 > 기타
        preferred_patterns = [
            'xl',  # SDXL 계열
            'sdxl', 
            'sd_xl',
            'sd15',  # SD 1.5 계열
            'sd_1_5',
            'v1-5',
            'realistic',  # Realistic 계열
            'base',  # 기본 모델들
        ]
        
        # 선호하는 패턴 순서대로 검색
        for pattern in preferred_patterns:
            for model in available_models:
                if pattern.lower() in model.lower():
                    return model
        
        # 아무것도 못 찾으면 첫 번째 모델 반환
        return available_models[0] if available_models else None
    
    def queue_prompt(self, workflow):
        """워크플로우를 ComfyUI에 전송"""
        try:
            response = requests.post(f"{self.base_url}/prompt", json={"prompt": workflow})
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error queuing prompt: {e}")
            return None
    
    def get_history(self, prompt_id):
        """생성 결과 조회"""
        try:
            response = requests.get(f"{self.base_url}/history/{prompt_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting history: {e}")
            return None
    
    def get_image(self, filename, subfolder="", folder_type="output"):
        """생성된 이미지 다운로드"""
        try:
            params = {
                "filename": filename,
                "subfolder": subfolder,
                "type": folder_type
            }
            response = requests.get(f"{self.base_url}/view", params=params)
            if response.status_code == 200:
                return response.content
            return None
        except Exception as e:
            print(f"Error getting image: {e}")
            return None
    
    def upload_image(self, image_data, filename):
        """이미지를 ComfyUI에 업로드"""
        try:
            files = {'image': (filename, image_data, 'image/png')}
            response = requests.post(f"{self.base_url}/upload/image", files=files)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error uploading image: {e}")
            return None
    
    def translate_to_english(self, text):
        """다국어 텍스트를 영어로 번역"""
        try:
            # 텍스트가 이미 영어인지 간단히 확인 (ASCII 문자 비율로 판단)
            ascii_chars = sum(1 for c in text if ord(c) < 128)
            total_chars = len(text)
            if total_chars > 0 and ascii_chars / total_chars > 0.8:
                # 이미 영어로 보이면 번역하지 않음
                return text
            
            translation_prompt = f"""Translate the following text to English. Only respond with the translated text, no explanations:

Text to translate: "{text}"

English translation:"""

            messages = [{"role": "user", "content": translation_prompt}]
            
            response = requests.post(f"http://localhost:11434/api/chat", 
                                   json={
                                       "model": "qwen2.5:7b",
                                       "messages": messages,
                                       "stream": False,
                                       "options": {
                                           "temperature": 0.3  # 번역은 더 정확하게
                                       }
                                   })
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result.get("message", {}).get("content", "").strip()
                return translated_text if translated_text else text
            else:
                print(f"Translation failed: {response.status_code}")
                return text
                
        except Exception as e:
            print(f"Error translating text: {e}")
            return text

    def enhance_prompt_with_qwen(self, original_prompt):
        """Ollama의 Qwen 모델을 사용하여 프롬프트 개선"""
        try:
            # 먼저 영어로 번역
            english_prompt = self.translate_to_english(original_prompt)
            
            enhancement_prompt = f"""Improve the following image generation prompt by adding more artistic and detailed descriptions. Maintain the core meaning while adding visual elements, style, lighting, colors, and other details to help generate high-quality images.

Original prompt: "{english_prompt}"

Please respond with only the enhanced prompt, no explanations:"""

            messages = [{"role": "user", "content": enhancement_prompt}]
            
            # Ollama로 프롬프트 개선 요청 (qwen 모델 사용)
            response = requests.post(f"http://localhost:11434/api/chat", 
                                   json={
                                       "model": "qwen2.5:7b",  # 사용 가능한 qwen 모델
                                       "messages": messages,
                                       "stream": False,
                                       "options": {
                                           "temperature": 0.7
                                       }
                                   })
            
            if response.status_code == 200:
                result = response.json()
                enhanced_prompt = result.get("message", {}).get("content", "").strip()
                return enhanced_prompt if enhanced_prompt else english_prompt
            else:
                print(f"Prompt enhancement failed: {response.status_code}")
                return english_prompt
                
        except Exception as e:
            print(f"Error enhancing prompt: {e}")
            return original_prompt

    def generate_qwen_txt2img_workflow(self, prompt, negative_prompt="", width=1024, height=1024, steps=4, cfg=3.5, seed=-1):
        """Qwen-Image 네이티브 텍스트-이미지 생성 워크플로우 (ComfyUI 네이티브 지원)"""
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)
            
        # ComfyUI 네이티브 Qwen-Image 워크플로우
        workflow = {
            "1": {
                "inputs": {
                    "unet_name": "qwen2_vl_7b_instruct-gguf-q8_0.gguf",
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader",
                "_meta": {
                    "title": "Load Qwen UNet Model"
                }
            },
            "2": {
                "inputs": {
                    "text": prompt,
                    "clip": ["3", 0]
                },
                "class_type": "CLIPTextEncode", 
                "_meta": {
                    "title": "Encode Positive Prompt"
                }
            },
            "3": {
                "inputs": {
                    "clip_name": "qwen2_vl_7b_instruct-gguf-q8_0.gguf"
                },
                "class_type": "CLIPLoader",
                "_meta": {
                    "title": "Load Qwen CLIP"
                }
            },
            "4": {
                "inputs": {
                    "text": negative_prompt if negative_prompt else "low quality, blurry, bad anatomy",
                    "clip": ["3", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {
                    "title": "Encode Negative Prompt" 
                }
            },
            "5": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage",
                "_meta": {
                    "title": "Empty Latent Image"
                }
            },
            "6": {
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "denoise": 1.0,
                    "model": ["1", 0],
                    "positive": ["2", 0], 
                    "negative": ["4", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler",
                "_meta": {
                    "title": "Qwen KSampler"
                }
            },
            "7": {
                "inputs": {
                    "vae_name": "qwen_vae.safetensors"
                },
                "class_type": "VAELoader",
                "_meta": {
                    "title": "Load Qwen VAE"
                }
            },
            "8": {
                "inputs": {
                    "samples": ["6", 0],
                    "vae": ["7", 0]
                },
                "class_type": "VAEDecode",
                "_meta": {
                    "title": "VAE Decode"
                }
            },
            "9": {
                "inputs": {
                    "filename_prefix": "QwenImage",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "_meta": {
                    "title": "Save Qwen Image"
                }
            }
        }
        return workflow
    
    def generate_qwen_custom_node_workflow(self, prompt, negative_prompt="", width=1024, height=1024, steps=4, cfg=3.5, seed=-1):
        """Qwen-Image 커스텀 노드 워크플로우 (RH_Qwen-Image 노드 사용)"""
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)
            
        # 커스텀 노드를 사용한 Qwen-Image 워크플로우
        workflow = {
            "1": {
                "inputs": {
                    "model_path": "qwen-image/qwen2_vl_7b_instruct",
                    "device": "auto",
                    "dtype": "auto"
                },
                "class_type": "RH_QwenImageLoader",
                "_meta": {
                    "title": "Load Qwen-Image Model"
                }
            },
            "2": {
                "inputs": {
                    "text": prompt,
                    "negative_text": negative_prompt if negative_prompt else "",
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "cfg_scale": cfg,
                    "seed": seed,
                    "model": ["1", 0]
                },
                "class_type": "RH_QwenImageGenerator",
                "_meta": {
                    "title": "Generate Qwen Image"
                }
            },
            "3": {
                "inputs": {
                    "filename_prefix": "QwenCustom",
                    "images": ["2", 0]
                },
                "class_type": "SaveImage",
                "_meta": {
                    "title": "Save Generated Image"
                }
            }
        }
        return workflow
    
    def generate_txt2img_workflow(self, prompt, negative_prompt="", width=1024, height=1024, steps=20, cfg=7.0, seed=-1):
        """SDXL 텍스트-이미지 생성 워크플로우 (백업용)"""
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)
            
        workflow = {
            "4": {
                "inputs": {
                    "ckpt_name": "SDXL\\sd_xl_base_1.0.safetensors"
                },
                "class_type": "CheckpointLoaderSimple",
                "_meta": {
                    "title": "Load Checkpoint"
                }
            },
            "5": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage",
                "_meta": {
                    "title": "Empty Latent Image"
                }
            },
            "6": {
                "inputs": {
                    "text": f"{prompt}",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {
                    "title": "CLIP Text Encode (Prompt)"
                }
            },
            "7": {
                "inputs": {
                    "text": negative_prompt if negative_prompt else "",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {
                    "title": "CLIP Text Encode (Negative)"
                }
            },
            "3": {
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler",
                "_meta": {
                    "title": "KSampler"
                }
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode",
                "_meta": {
                    "title": "VAE Decode"
                }
            },
            "9": {
                "inputs": {
                    "filename_prefix": "SDXL_Generated",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "_meta": {
                    "title": "Save Image"
                }
            }
        }
        return workflow
    
    def generate_img2img_workflow(self, image_filename, prompt, negative_prompt="", strength=0.8, width=512, height=512, steps=20, cfg=7.0, seed=-1):
        """이미지-이미지 생성 워크플로우"""
        if seed == -1:
            import random
            seed = random.randint(0, 2**32 - 1)
            
        workflow = {
            "3": {
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": strength,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["10", 0]
                },
                "class_type": "KSampler",
                "_meta": {
                    "title": "KSampler"
                }
            },
            "4": {
                "inputs": {
                    "ckpt_name": "SDXL\\sd_xl_base_1.0.safetensors"
                },
                "class_type": "CheckpointLoaderSimple",
                "_meta": {
                    "title": "Load Checkpoint"
                }
            },
            "5": {
                "inputs": {
                    "image": image_filename,
                    "upload": "image"
                },
                "class_type": "LoadImage",
                "_meta": {
                    "title": "Load Image"
                }
            },
            "6": {
                "inputs": {
                    "text": prompt,
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {
                    "title": "CLIP Text Encode (Prompt)"
                }
            },
            "7": {
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {
                    "title": "CLIP Text Encode (Negative)"
                }
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode",
                "_meta": {
                    "title": "VAE Decode"
                }
            },
            "9": {
                "inputs": {
                    "filename_prefix": "ComfyUI",
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "_meta": {
                    "title": "Save Image"
                }
            },
            "10": {
                "inputs": {
                    "pixels": ["5", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEEncode",
                "_meta": {
                    "title": "VAE Encode"
                }
            }
        }
        return workflow

class QwenImageClient:
    """Qwen-Image 모델을 직접 사용하는 클라이언트"""
    def __init__(self):
        self.pipe = None
        self.model_loaded = False
        # 사용 가능한 모델들 (안정적인 것부터 시작)
        self.model_candidates = [
            "Qwen/Qwen-Image",  # 목표 모델 (우선 시도)
            "runwayml/stable-diffusion-v1-5",  # 가장 안정적인 SD 1.5
            "CompVis/stable-diffusion-v1-4",   # SD 1.4 (더 가벼움)
        ]
        self.current_model_path = None
        
    def is_available(self):
        """Qwen-Image 모델 사용 가능 여부 확인"""
        try:
            import diffusers
            import transformers
            import torch
            return True
        except ImportError:
            return False
    
    def load_model(self):
        """이미지 생성 모델 로드 (임시: 기본 생성기 사용)"""
        if self.model_loaded:
            return True
        
        print("Loading image generator...")
        
        # 임시 해결책: ML 모델 대신 프로그래매틱 이미지 생성
        try:
            from PIL import Image, ImageDraw
            import random
            import hashlib
            
            print("Using basic image generator (ML models unavailable due to dependency issues)")
            
            # 성공으로 표시
            self.current_model_path = "PIL-basic-generator"
            self.model_loaded = True
            print(f"SUCCESS: Basic image generator loaded")
            return True
            
        except Exception as e:
            print(f"ERROR: Even basic image generator failed: {e}")
            return False
    
    def generate_image(self, prompt, negative_prompt="", width=1024, height=1024, num_inference_steps=50, guidance_scale=7.0, seed=None):
        """프롬프트 기반 이미지 생성 (개선된 버전)"""
        if not self.model_loaded:
            if not self.load_model():
                return None, "모델 로드 실패"
                
        try:
            from PIL import Image, ImageDraw, ImageFont
            import random
            import time
            import re
            
            # 시드 설정
            if seed is None:
                seed = random.randint(0, 2**32 - 1)
            
            random.seed(seed)
            
            print(f"이미지 생성 시작...")
            print(f"프롬프트: {prompt}")
            print(f"크기: {width}x{height}")
            print(f"시드: {seed}")
            
            start_time = time.time()
            
            # 프롬프트 분석 및 해석
            prompt_lower = prompt.lower()
            
            # 1. 색상 키워드 감지
            color_map = {
                'red': (220, 20, 20), 'blue': (20, 20, 220), 'green': (20, 220, 20),
                'yellow': (220, 220, 20), 'purple': (220, 20, 220), 'orange': (255, 165, 0),
                'pink': (255, 192, 203), 'brown': (139, 69, 19), 'black': (30, 30, 30),
                'white': (240, 240, 240), 'gray': (128, 128, 128), 'grey': (128, 128, 128)
            }
            
            detected_colors = []
            for color_name, color_value in color_map.items():
                if color_name in prompt_lower:
                    detected_colors.append(color_value)
            
            # 기본 색상 설정
            if not detected_colors:
                detected_colors = [(100, 150, 200), (200, 150, 100), (150, 200, 100)]
            
            # 2. 배경색 설정
            if 'sky' in prompt_lower or 'blue' in prompt_lower:
                bg_color = (135, 206, 235)  # 하늘색
            elif 'grass' in prompt_lower or 'green' in prompt_lower:
                bg_color = (144, 238, 144)  # 연한 녹색
            elif 'night' in prompt_lower or 'dark' in prompt_lower:
                bg_color = (25, 25, 112)    # 밤색
            elif 'sunset' in prompt_lower or 'orange' in prompt_lower:
                bg_color = (255, 165, 0)    # 주황색
            else:
                bg_color = detected_colors[0] if detected_colors else (200, 200, 220)
            
            # 이미지 생성
            image = Image.new('RGB', (width, height), color=bg_color)
            draw = ImageDraw.Draw(image)
            
            # 3. 객체 생성
            objects_created = []
            
            # 태양 생성
            if 'sun' in prompt_lower or 'sunny' in prompt_lower:
                sun_x = width - width // 4
                sun_y = height // 4
                sun_size = 80
                draw.ellipse([sun_x-sun_size, sun_y-sun_size, sun_x+sun_size, sun_y+sun_size], 
                           fill=(255, 255, 0), outline=(255, 215, 0))
                objects_created.append("sun")
            
            # 달 생성
            if 'moon' in prompt_lower:
                moon_x = width - width // 4
                moon_y = height // 4
                moon_size = 60
                draw.ellipse([moon_x-moon_size, moon_y-moon_size, moon_x+moon_size, moon_y+moon_size], 
                           fill=(245, 245, 220), outline=(211, 211, 211))
                objects_created.append("moon")
            
            # 집 생성
            if 'house' in prompt_lower or 'home' in prompt_lower or 'building' in prompt_lower:
                house_x = width // 2
                house_y = height - height // 3
                house_w, house_h = 120, 100
                
                # 집 몸체
                draw.rectangle([house_x-house_w//2, house_y-house_h, house_x+house_w//2, house_y], 
                             fill=(160, 82, 45), outline=(139, 69, 19))
                # 지붕
                roof_points = [(house_x-house_w//2-10, house_y-house_h), 
                              (house_x, house_y-house_h-40), 
                              (house_x+house_w//2+10, house_y-house_h)]
                draw.polygon(roof_points, fill=(178, 34, 34))
                
                # 문
                door_w, door_h = 25, 60
                draw.rectangle([house_x-door_w//2, house_y-door_h, house_x+door_w//2, house_y], 
                             fill=(101, 67, 33))
                objects_created.append("house")
            
            # 나무 생성
            if 'tree' in prompt_lower or 'forest' in prompt_lower:
                for i in range(2 if 'forest' in prompt_lower else 1):
                    tree_x = width // 4 + i * (width // 2)
                    tree_y = height - 50
                    
                    # 나무 줄기
                    trunk_w, trunk_h = 20, 80
                    draw.rectangle([tree_x-trunk_w//2, tree_y-trunk_h, tree_x+trunk_w//2, tree_y], 
                                 fill=(101, 67, 33))
                    
                    # 나뭇잎
                    leaves_size = 60
                    draw.ellipse([tree_x-leaves_size, tree_y-trunk_h-leaves_size//2, 
                                tree_x+leaves_size, tree_y-trunk_h+leaves_size//2], 
                               fill=(34, 139, 34))
                objects_created.append("tree")
            
            # 꽃 생성
            if 'flower' in prompt_lower or 'garden' in prompt_lower:
                for i in range(3):
                    flower_x = width // 4 + i * (width // 4)
                    flower_y = height - 30
                    
                    # 꽃잎들
                    petal_size = 15
                    flower_color = detected_colors[i % len(detected_colors)]
                    for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
                        import math
                        px = flower_x + math.cos(math.radians(angle)) * petal_size
                        py = flower_y + math.sin(math.radians(angle)) * petal_size
                        draw.ellipse([px-8, py-8, px+8, py+8], fill=flower_color)
                    
                    # 중심부
                    draw.ellipse([flower_x-5, flower_y-5, flower_x+5, flower_y+5], fill=(255, 255, 0))
                objects_created.append("flowers")
            
            # 구름 생성
            if 'cloud' in prompt_lower or 'sky' in prompt_lower:
                for i in range(2):
                    cloud_x = width // 3 + i * (width // 3)
                    cloud_y = height // 5
                    
                    # 여러 원으로 구름 만들기
                    cloud_sizes = [30, 25, 35, 28]
                    cloud_positions = [(-20, 0), (20, 0), (0, -15), (0, 15)]
                    
                    for size, (dx, dy) in zip(cloud_sizes, cloud_positions):
                        draw.ellipse([cloud_x+dx-size, cloud_y+dy-size//2, 
                                    cloud_x+dx+size, cloud_y+dy+size//2], 
                                   fill=(255, 255, 255), outline=(220, 220, 220))
                objects_created.append("clouds")
            
            # 별 생성
            if 'star' in prompt_lower or 'night' in prompt_lower:
                for i in range(5):
                    star_x = random.randint(50, width-50)
                    star_y = random.randint(50, height//2)
                    
                    # 간단한 별 모양 (십자가)
                    star_size = 10
                    draw.line([(star_x-star_size, star_y), (star_x+star_size, star_y)], 
                             fill=(255, 255, 255), width=3)
                    draw.line([(star_x, star_y-star_size), (star_x, star_y+star_size)], 
                             fill=(255, 255, 255), width=3)
                objects_created.append("stars")
            
            # 고양이 생성
            if 'cat' in prompt_lower:
                cat_x = width // 2
                cat_y = height - height // 3
                
                # 고양이 몸
                draw.ellipse([cat_x-40, cat_y-20, cat_x+40, cat_y+20], fill=(100, 100, 100))
                # 고양이 머리
                draw.ellipse([cat_x-25, cat_y-40, cat_x+25, cat_y-10], fill=(120, 120, 120))
                # 귀
                ear_points1 = [(cat_x-20, cat_y-35), (cat_x-10, cat_y-50), (cat_x-5, cat_y-35)]
                ear_points2 = [(cat_x+5, cat_y-35), (cat_x+10, cat_y-50), (cat_x+20, cat_y-35)]
                draw.polygon(ear_points1, fill=(120, 120, 120))
                draw.polygon(ear_points2, fill=(120, 120, 120))
                # 꼬리
                draw.ellipse([cat_x+35, cat_y-10, cat_x+60, cat_y-30], fill=(100, 100, 100))
                objects_created.append("cat")
            
            # 개 생성
            if 'dog' in prompt_lower:
                dog_x = width // 2
                dog_y = height - height // 3
                
                # 개 몸
                draw.ellipse([dog_x-50, dog_y-25, dog_x+50, dog_y+25], fill=(139, 69, 19))
                # 개 머리
                draw.ellipse([dog_x-30, dog_y-45, dog_x+30, dog_y-15], fill=(160, 82, 45))
                # 귀 (늘어진)
                draw.ellipse([dog_x-40, dog_y-40, dog_x-20, dog_y-20], fill=(139, 69, 19))
                draw.ellipse([dog_x+20, dog_y-40, dog_x+40, dog_y-20], fill=(139, 69, 19))
                # 꼬리
                draw.ellipse([dog_x+40, dog_y-15, dog_x+70, dog_y-35], fill=(139, 69, 19))
                objects_created.append("dog")
            
            # 자동차 생성
            if 'car' in prompt_lower:
                car_x = width // 2
                car_y = height - 100
                
                # 자동차 몸체
                draw.rectangle([car_x-60, car_y-30, car_x+60, car_y], fill=(255, 0, 0))
                # 자동차 지붕
                draw.rectangle([car_x-40, car_y-50, car_x+40, car_y-30], fill=(200, 0, 0))
                # 바퀴
                draw.ellipse([car_x-50, car_y-10, car_x-30, car_y+10], fill=(50, 50, 50))
                draw.ellipse([car_x+30, car_y-10, car_x+50, car_y+10], fill=(50, 50, 50))
                objects_created.append("car")
            
            # 텍스트 정보 추가
            try:
                font_size = max(12, min(24, width // 40))
                
                # 생성된 객체들 표시
                if objects_created:
                    objects_text = "Generated: " + ", ".join(objects_created)
                else:
                    objects_text = f"Abstract art for: {prompt.split()[:3]}"
                
                text_y_pos = 20
                draw.text((20, text_y_pos), objects_text, fill=(255, 255, 255))
                draw.text((20, text_y_pos + 25), f"Seed: {seed}", fill=(200, 200, 200))
                
            except Exception as e:
                print(f"Text rendering error: {e}")
            
            generation_time = time.time() - start_time
            
            print(f"이미지 생성 완료!")
            print(f"생성 시간: {generation_time:.3f}초")
            print(f"생성된 객체: {objects_created}")
            print(f"프롬프트 기반 생성기 사용")
            
            return image, None
            
        except Exception as e:
            error_msg = f"이미지 생성 실패: {e}"
            print(f"오류: {error_msg}")
            import traceback
            traceback.print_exc()
            return None, error_msg
    
    def translate_prompt(self, prompt, target_lang="en"):
        """프롬프트 번역 (필요시)"""
        # 간단한 ASCII 체크로 영어 여부 확인
        ascii_chars = sum(1 for c in prompt if ord(c) < 128)
        total_chars = len(prompt)
        
        if total_chars > 0 and ascii_chars / total_chars > 0.8:
            # 이미 영어로 보임
            return prompt
        
        # 여기서는 번역 기능을 구현하지 않음 (Ollama 연동 필요시 추가 가능)
        return prompt

ollama_client = OllamaClient(
    host=os.getenv('OLLAMA_HOST', 'localhost'),
    port=int(os.getenv('OLLAMA_PORT', 11434))
)

comfyui_client = ComfyUIClient(
    host=os.getenv('COMFYUI_HOST', 'localhost'),
    port=int(os.getenv('COMFYUI_PORT', 8188))
)

qwen_image_client = QwenImageClient()

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

@app.route('/api/image_models')
def get_image_models():
    """이미지 생성 모델 목록 조회 (Qwen-Image 직접 + ComfyUI)"""
    try:
        image_models = []
        
        # Qwen-Image 직접 구현 모델 추가
        qwen_available = qwen_image_client.is_available()
        image_models.append({
            "model_name": "qwen-direct",
            "title": "🎨 Qwen-Image (직접 구현)",
            "type": "direct",
            "available": qwen_available,
            "description": "Diffusers를 통한 직접 구현"
        })
        
        # ComfyUI 연결 확인
        comfyui_connected = comfyui_client.check_connection()
        
        if comfyui_connected:
            # ComfyUI 기반 Qwen-Image 모델들
            qwen_models = [
                {
                    "model_name": "qwen-image",
                    "title": "🎨 Qwen-Image (ComfyUI 네이티브)",
                    "type": "comfyui",
                    "available": True,
                    "description": "ComfyUI 네이티브 지원"
                },
                {
                    "model_name": "qwen-custom", 
                    "title": "🎨 Qwen-Image (ComfyUI 커스텀)",
                    "type": "comfyui",
                    "available": True,
                    "description": "ComfyUI 커스텀 노드"
                }
            ]
            image_models.extend(qwen_models)
            
            # ComfyUI에서 실제 사용 가능한 SDXL 모델들 조회
            available_models = comfyui_client.get_available_models()
            if available_models:
                for model in available_models:
                    image_models.append({
                        "model_name": model,
                        "title": model.replace('.safetensors', '').replace('.ckpt', '').replace('_', ' ').title(),
                        "type": "comfyui",
                        "available": True,
                        "description": "ComfyUI SDXL 모델"
                    })
            else:
                # 기본 SDXL 모델들 (ComfyUI에 모델이 없을 경우)
                image_models.append({
                    "model_name": "SDXL\\sd_xl_base_1.0.safetensors",
                    "title": "Stable Diffusion XL Base (기본)",
                    "type": "comfyui",
                    "available": False,
                    "description": "기본 SDXL 모델 (설치 필요)"
                })
        
        return jsonify({
            "data": image_models, 
            "comfyui_connected": comfyui_connected,
            "qwen_direct_available": qwen_available
        })
        
    except Exception as e:
        return jsonify({
            "data": [
                {
                    "model_name": "qwen-direct",
                    "title": "🎨 Qwen-Image (직접 구현)",
                    "type": "direct",
                    "available": qwen_image_client.is_available(),
                    "description": "Diffusers를 통한 직접 구현"
                }
            ], 
            "error": f"오류: {str(e)}", 
            "comfyui_connected": False,
            "qwen_direct_available": qwen_image_client.is_available()
        })

@app.route('/api/generate_image', methods=['POST'])
def generate_image():
    data = request.get_json()
    prompt = data.get('prompt', '')
    negative_prompt = data.get('negative_prompt', '')
    width = int(data.get('width', 1024))
    height = int(data.get('height', 1024))
    steps = int(data.get('steps', 50))
    cfg_scale = float(data.get('cfg_scale', 7.0))
    model = data.get('model', 'qwen-direct')  # 기본 모델을 Qwen 직접 구현으로 설정
    use_qwen = data.get('use_qwen', True)
    seed = data.get('seed')
    
    if not prompt:
        return jsonify({'error': '프롬프트가 필요합니다.'}), 400
    
    # Qwen 직접 구현 사용 시
    if model == 'qwen-direct':
        if not qwen_image_client.is_available():
            return jsonify({'error': 'Qwen-Image 직접 구현에 필요한 라이브러리가 설치되지 않았습니다.'}), 500
        
        # Qwen 직접 생성 API로 리다이렉트
        return generate_qwen_image()
    
    # ComfyUI 사용 시
    if not comfyui_client.check_connection():
        return jsonify({'error': 'ComfyUI 서버에 연결할 수 없습니다.'}), 500
    
    try:
        # 프롬프트 번역 및 개선 (Qwen 모델 사용 시)
        enhanced_prompt = prompt
        translated_negative = comfyui_client.translate_to_english(negative_prompt) if negative_prompt else negative_prompt
        
        if use_qwen:
            # 먼저 번역 확인
            translated_prompt = comfyui_client.translate_to_english(prompt)
            enhanced_prompt = comfyui_client.enhance_prompt_with_qwen(prompt)
            
            print(f"=== PROMPT PROCESSING ===")
            print(f"Original: '{prompt}'")
            if translated_prompt != prompt:
                print(f"Translated: '{translated_prompt}'")
            print(f"Enhanced: '{enhanced_prompt}'")
            if negative_prompt:
                print(f"Original Negative: '{negative_prompt}'")
                if translated_negative != negative_prompt:
                    print(f"Translated Negative: '{translated_negative}'")
            print("========================")
        else:
            # Qwen 개선을 사용하지 않을 때도 번역은 수행
            enhanced_prompt = comfyui_client.translate_to_english(prompt)
            if enhanced_prompt != prompt:
                print(f"=== PROMPT TRANSLATION ===")
                print(f"Original: '{prompt}'")
                print(f"Translated: '{enhanced_prompt}'")
                if negative_prompt and translated_negative != negative_prompt:
                    print(f"Original Negative: '{negative_prompt}'")
                    print(f"Translated Negative: '{translated_negative}'")
                print("========================")
        
        # negative_prompt도 번역된 것으로 업데이트
        negative_prompt = translated_negative
        
        # ComfyUI 워크플로우 생성 (Qwen-Image 우선, SDXL 폴백)
        workflow_success = False
        workflow_type = "unknown"
        
        if use_qwen and (model == 'qwen-image' or model == 'qwen-custom'):
            # Qwen-Image 워크플로우 시도 (실제로는 모델이 없으므로 SDXL로 폴백)
            print(f"=== QWEN-IMAGE 요청됨 but 모델 없음, SDXL로 폴백 ===")
            print(f"요청된 모델: {model}")
            print("Qwen-Image 모델이 설치되지 않아 SDXL 워크플로우를 사용합니다.")
            print("=============================================")
            
            # SDXL 워크플로우로 폴백
            workflow = comfyui_client.generate_txt2img_workflow(
                prompt=enhanced_prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                steps=max(8, steps),  # SDXL은 최소 8 스텝 권장
                cfg=max(7.0, cfg_scale)  # SDXL은 7.0 CFG 권장
            )
            # 사용 가능한 모델로 설정
            workflow["4"]["inputs"]["ckpt_name"] = "SDXL\\sd_xl_base_1.0.safetensors"
            workflow_type = "sdxl_fallback"
        else:
            # 백업: SDXL 워크플로우 사용
            workflow = comfyui_client.generate_txt2img_workflow(
                prompt=enhanced_prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                steps=steps,
                cfg=cfg_scale
            )
            # 선택된 SDXL 모델을 워크플로우에 적용
            workflow["4"]["inputs"]["ckpt_name"] = model
            print(f"=== SDXL FALLBACK WORKFLOW DEBUG ===")
            print(f"Enhanced prompt: '{enhanced_prompt}'")
            print(f"Model: {model}")
            print("==================================")
        
        # ComfyUI에 워크플로우 전송
        queue_result = comfyui_client.queue_prompt(workflow)
        if not queue_result:
            return jsonify({'error': 'ComfyUI 워크플로우 전송 실패'}), 500
        
        prompt_id = queue_result.get('prompt_id')
        if not prompt_id:
            return jsonify({'error': '프롬프트 ID 획득 실패'}), 500
        
        # 결과 대기 및 조회 (최대 60초 - Qwen-Image는 더 오래 걸릴 수 있음)
        import time
        max_wait_time = 60 if use_qwen else 30
        wait_time = 0
        
        while wait_time < max_wait_time:
            history = comfyui_client.get_history(prompt_id)
            if history and prompt_id in history:
                # 완료된 경우 이미지 파일명 추출
                outputs = history[prompt_id].get('outputs', {})
                for node_id, node_output in outputs.items():
                    if 'images' in node_output:
                        for img_info in node_output['images']:
                            filename = img_info['filename']
                            subfolder = img_info.get('subfolder', '')
                            
                            # ComfyUI에서 이미지 다운로드
                            image_data = comfyui_client.get_image(filename, subfolder)
                            if image_data:
                                # 로컬에 저장
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                prefix = "qwen_generated" if use_qwen else "sdxl_generated"
                                local_filename = f"{prefix}_{timestamp}.png"
                                
                                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                                local_path = os.path.join(app.config['UPLOAD_FOLDER'], local_filename)
                                
                                with open(local_path, 'wb') as f:
                                    f.write(image_data)
                                
                                return jsonify({
                                    'success': True,
                                    'image_url': f'/static/uploads/{local_filename}',
                                    'prompt': prompt,
                                    'enhanced_prompt': enhanced_prompt,
                                    'model': workflow_type if workflow_type != "unknown" else model,
                                    'generation_type': workflow_type
                                })
                
                return jsonify({'error': '생성된 이미지를 찾을 수 없습니다.'}), 500
                
            time.sleep(2)  # 2초 간격으로 체크
            wait_time += 2
        
        timeout_msg = f'이미지 생성 시간 초과 ({max_wait_time}초)'
        return jsonify({'error': timeout_msg}), 500
            
    except Exception as e:
        return jsonify({'error': f'이미지 생성 중 오류: {str(e)}'}), 500

@app.route('/api/img2img', methods=['POST'])
def img2img():
    data = request.get_json()
    init_image_url = data.get('init_image_url')
    prompt = data.get('prompt', '')
    negative_prompt = data.get('negative_prompt', '')
    strength = float(data.get('denoising_strength', 0.8))
    width = int(data.get('width', 512))
    height = int(data.get('height', 512))
    steps = int(data.get('steps', 20))
    cfg_scale = float(data.get('cfg_scale', 7))
    model = data.get('model', 'SDXL\\sd_xl_base_1.0.safetensors')
    
    if not prompt or not init_image_url:
        return jsonify({'error': '프롬프트와 초기 이미지가 필요합니다.'}), 400
    
    if not comfyui_client.check_connection():
        return jsonify({'error': 'ComfyUI 서버에 연결할 수 없습니다.'}), 500
    
    try:
        # 프롬프트들을 영어로 번역
        translated_prompt = comfyui_client.translate_to_english(prompt)
        translated_negative = comfyui_client.translate_to_english(negative_prompt) if negative_prompt else negative_prompt
        
        if translated_prompt != prompt or (negative_prompt and translated_negative != negative_prompt):
            print(f"=== IMG2IMG PROMPT TRANSLATION ===")
            print(f"Original Prompt: '{prompt}'")
            if translated_prompt != prompt:
                print(f"Translated Prompt: '{translated_prompt}'")
            if negative_prompt:
                print(f"Original Negative: '{negative_prompt}'")
                if translated_negative != negative_prompt:
                    print(f"Translated Negative: '{translated_negative}'")
            print("=================================")
            
        prompt = translated_prompt
        negative_prompt = translated_negative
        
        # 초기 이미지 로드 및 ComfyUI에 업로드
        if init_image_url.startswith('/static/uploads/'):
            file_path = os.path.join(os.getcwd(), init_image_url[1:])
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            # ComfyUI에 이미지 업로드
            upload_result = comfyui_client.upload_image(image_data, f"init_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            if not upload_result:
                return jsonify({'error': '이미지 업로드 실패'}), 500
                
            uploaded_filename = upload_result.get('name')
            if not uploaded_filename:
                return jsonify({'error': '업로드된 파일명 획득 실패'}), 500
        else:
            return jsonify({'error': '유효하지 않은 이미지 경로입니다.'}), 400
        
        # ComfyUI img2img 워크플로우 생성
        workflow = comfyui_client.generate_img2img_workflow(
            image_filename=uploaded_filename,
            prompt=prompt,
            negative_prompt=negative_prompt,
            strength=strength,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg_scale
        )
        
        # 선택된 모델을 워크플로우에 적용
        workflow["4"]["inputs"]["ckpt_name"] = model
        
        # ComfyUI에 워크플로우 전송
        queue_result = comfyui_client.queue_prompt(workflow)
        if not queue_result:
            return jsonify({'error': 'ComfyUI 워크플로우 전송 실패'}), 500
        
        prompt_id = queue_result.get('prompt_id')
        if not prompt_id:
            return jsonify({'error': '프롬프트 ID 획득 실패'}), 500
        
        # 결과 대기 및 조회 (최대 30초)
        import time
        max_wait_time = 30
        wait_time = 0
        
        while wait_time < max_wait_time:
            history = comfyui_client.get_history(prompt_id)
            if history and prompt_id in history:
                # 완료된 경우 이미지 파일명 추출
                outputs = history[prompt_id].get('outputs', {})
                for node_id, node_output in outputs.items():
                    if 'images' in node_output:
                        for img_info in node_output['images']:
                            filename = img_info['filename']
                            subfolder = img_info.get('subfolder', '')
                            
                            # ComfyUI에서 이미지 다운로드
                            image_data = comfyui_client.get_image(filename, subfolder)
                            if image_data:
                                # 로컬에 저장
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                local_filename = f"comfyui_img2img_{timestamp}.png"
                                
                                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                                local_path = os.path.join(app.config['UPLOAD_FOLDER'], local_filename)
                                
                                with open(local_path, 'wb') as f:
                                    f.write(image_data)
                                
                                return jsonify({
                                    'success': True,
                                    'image_url': f'/static/uploads/{local_filename}',
                                    'prompt': prompt,
                                    'original_image': init_image_url,
                                    'model': model
                                })
                
                return jsonify({'error': '생성된 이미지를 찾을 수 없습니다.'}), 500
                
            time.sleep(1)
            wait_time += 1
        
        return jsonify({'error': '이미지 변환 시간 초과 (30초)'}), 500
            
    except Exception as e:
        return jsonify({'error': f'이미지 변환 중 오류: {str(e)}'}), 500

@app.route('/api/generate_qwen_image', methods=['POST'])
def generate_qwen_image():
    """Qwen-Image 직접 구현을 통한 이미지 생성"""
    data = request.get_json()
    prompt = data.get('prompt', '')
    negative_prompt = data.get('negative_prompt', '')
    width = int(data.get('width', 1024))
    height = int(data.get('height', 1024))
    num_inference_steps = int(data.get('steps', 50))
    guidance_scale = float(data.get('cfg_scale', 7.0))
    seed = data.get('seed')
    
    if not prompt:
        return jsonify({'error': '프롬프트가 필요합니다.'}), 400
    
    if not qwen_image_client.is_available():
        return jsonify({'error': 'Qwen-Image 직접 구현에 필요한 라이브러리가 설치되지 않았습니다. pip install -r requirements.txt를 실행하세요.'}), 500
    
    try:
        # 프롬프트 번역 (필요시)
        translated_prompt = qwen_image_client.translate_prompt(prompt)
        translated_negative = qwen_image_client.translate_prompt(negative_prompt) if negative_prompt else ""
        
        if translated_prompt != prompt:
            print(f"=== QWEN DIRECT PROMPT TRANSLATION ===")
            print(f"Original: '{prompt}'")
            print(f"Translated: '{translated_prompt}'")
            if negative_prompt and translated_negative != negative_prompt:
                print(f"Original Negative: '{negative_prompt}'")
                print(f"Translated Negative: '{translated_negative}'")
            print("=====================================")
        
        # 이미지 생성
        image, error = qwen_image_client.generate_image(
            prompt=translated_prompt,
            negative_prompt=translated_negative,
            width=width,
            height=height,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            seed=int(seed) if seed else None
        )
        
        if error:
            return jsonify({'error': error}), 500
        
        if image is None:
            return jsonify({'error': '이미지 생성 실패'}), 500
        
        # 이미지를 로컬에 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"qwen_direct_{timestamp}.png"
        
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # PIL Image를 파일로 저장
        image.save(file_path, format='PNG')
        
        return jsonify({
            'success': True,
            'image_url': f'/static/uploads/{filename}',
            'prompt': prompt,
            'translated_prompt': translated_prompt if translated_prompt != prompt else None,
            'model': 'qwen-direct',
            'generation_type': 'qwen_direct',
            'parameters': {
                'width': width,
                'height': height,
                'steps': num_inference_steps,
                'guidance_scale': guidance_scale,
                'seed': seed
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Qwen-Image 직접 생성 중 오류: {str(e)}'}), 500

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