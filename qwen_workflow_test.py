#!/usr/bin/env python3
"""Qwen-Image 워크플로우 테스트 스크립트"""

import json
from app import ComfyUIClient

def test_qwen_workflows():
    """Qwen-Image 워크플로우들을 테스트하고 JSON으로 출력"""
    
    client = ComfyUIClient()
    
    # 테스트 파라미터
    test_prompt = "A beautiful landscape with cherry blossoms, highly detailed, photorealistic"
    negative_prompt = "low quality, blurry, bad anatomy"
    
    print("=== Qwen-Image 네이티브 워크플로우 ===")
    native_workflow = client.generate_qwen_txt2img_workflow(
        prompt=test_prompt,
        negative_prompt=negative_prompt,
        width=1024,
        height=1024,
        steps=4,
        cfg=3.5
    )
    print(json.dumps(native_workflow, indent=2, ensure_ascii=False))
    
    print("\n=== Qwen-Image 커스텀 노드 워크플로우 ===")
    custom_workflow = client.generate_qwen_custom_node_workflow(
        prompt=test_prompt,
        negative_prompt=negative_prompt,
        width=1024,
        height=1024,
        steps=4,
        cfg=3.5
    )
    print(json.dumps(custom_workflow, indent=2, ensure_ascii=False))
    
    print("\n=== 워크플로우 생성 완료 ===")
    print("ComfyUI에서 이 워크플로우들을 사용할 수 있습니다.")
    print("필요한 모델 파일:")
    print("1. 네이티브 워크플로우: qwen2_vl_7b_instruct-gguf-q8_0.gguf, qwen_vae.safetensors")
    print("2. 커스텀 노드 워크플로우: RH_QwenImage 커스텀 노드 설치 필요")

if __name__ == "__main__":
    test_qwen_workflows()