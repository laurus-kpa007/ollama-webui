#!/usr/bin/env python3
"""ComfyUI 워크플로우 테스트 스크립트"""

import requests
import json
import time

def test_comfyui_workflow():
    """기본 SDXL 워크플로우로 ComfyUI 테스트"""
    
    base_url = "http://localhost:8188"
    
    # 간단한 SDXL 워크플로우
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
                "width": 512,
                "height": 512,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage",
            "_meta": {
                "title": "Empty Latent Image"
            }
        },
        "6": {
            "inputs": {
                "text": "a beautiful cat, highly detailed",
                "clip": ["4", 1]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {
                "title": "CLIP Text Encode (Prompt)"
            }
        },
        "7": {
            "inputs": {
                "text": "low quality, blurry",
                "clip": ["4", 1]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {
                "title": "CLIP Text Encode (Negative)"
            }
        },
        "3": {
            "inputs": {
                "seed": 12345,
                "steps": 8,
                "cfg": 7.0,
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
                "filename_prefix": "Test",
                "images": ["8", 0]
            },
            "class_type": "SaveImage",
            "_meta": {
                "title": "Save Image"
            }
        }
    }
    
    print("=== ComfyUI 워크플로우 테스트 ===")
    print(f"워크플로우 JSON:")
    print(json.dumps(workflow, indent=2, ensure_ascii=False))
    
    try:
        # ComfyUI에 워크플로우 전송
        response = requests.post(f"{base_url}/prompt", json={"prompt": workflow})
        print(f"\n응답 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            prompt_id = result.get('prompt_id')
            print(f"성공! Prompt ID: {prompt_id}")
            return True
        else:
            print(f"실패: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"오류 발생: {e}")
        return False

if __name__ == "__main__":
    test_comfyui_workflow()