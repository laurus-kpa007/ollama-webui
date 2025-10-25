#!/usr/bin/env python3
"""이미지 생성 API 테스트 스크립트"""

import requests
import json

def test_image_generation():
    """수정된 이미지 생성 API 테스트"""
    
    api_url = "http://localhost:5000/api/generate_image"
    
    # 테스트 데이터
    test_data = {
        "prompt": "a beautiful cat sitting on a chair",
        "negative_prompt": "low quality, blurry",
        "width": 512,
        "height": 512,
        "steps": 8,
        "cfg_scale": 7.0,
        "model": "qwen-image",  # Qwen 요청하지만 SDXL로 폴백될 것
        "use_qwen": True
    }
    
    print("=== 이미지 생성 API 테스트 ===")
    print(f"요청 데이터:")
    print(json.dumps(test_data, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(api_url, json=test_data)
        print(f"\n응답 상태 코드: {response.status_code}")
        print(f"응답 내용:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"\n✅ 성공! 이미지 URL: {result.get('image_url')}")
                print(f"사용된 모델: {result.get('model')}")
                print(f"생성 타입: {result.get('generation_type')}")
                return True
            else:
                print(f"\n❌ 실패: {result.get('error')}")
                return False
        else:
            print(f"\n❌ HTTP 오류: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        return False

if __name__ == "__main__":
    test_image_generation()