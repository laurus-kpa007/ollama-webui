# Qwen-Image 설정 가이드

이 가이드는 ComfyUI에서 Qwen-Image 모델을 사용하기 위한 설정 방법을 설명합니다.

## 🎯 주요 특징

- **다국어 텍스트 렌더링**: 한국어, 중국어, 일본어, 영어 등 다양한 언어의 텍스트를 이미지에 정확하게 렌더링
- **빠른 생성 속도**: 4 스텝만으로 고품질 이미지 생성 가능
- **예술적 다양성**: 사진, 애니메이션, 회화 등 다양한 스타일 지원
- **정확한 프롬프트 이해**: 복잡한 설명도 정확하게 이미지로 변환

## 📋 시스템 요구사항

### 최소 요구사항 (GGUF 버전)
- **GPU**: 12GB VRAM 이상
- **RAM**: 32GB 이상
- **저장공간**: 15GB 이상

### 권장 요구사항 (전체 버전)
- **GPU**: 24GB VRAM 이상 (RTX 4090, RTX A5000 등)
- **RAM**: 64GB 이상
- **저장공간**: 50GB 이상

## 🚀 설치 방법

### 방법 1: ComfyUI 네이티브 지원 사용

1. **ComfyUI 업데이트**
   ```bash
   cd ComfyUI
   git pull
   ```

2. **Qwen-Image 모델 다운로드**
   - [Hugging Face - Qwen-Image](https://huggingface.co/Qwen/Qwen-Image)에서 모델 다운로드
   - GGUF 버전 권장: `qwen2_vl_7b_instruct-gguf-q8_0.gguf`

3. **모델 파일 배치**
   ```
   ComfyUI/
   ├── models/
   │   ├── unet/
   │   │   └── qwen2_vl_7b_instruct-gguf-q8_0.gguf
   │   ├── clip/
   │   │   └── qwen2_vl_7b_instruct-gguf-q8_0.gguf
   │   └── vae/
   │       └── qwen_vae.safetensors
   ```

4. **GGUF 지원 노드 설치 (필요시)**
   - ComfyUI Manager에서 "ComfyUI-GGUF" 검색하여 설치

### 방법 2: RH_Qwen-Image 커스텀 노드 사용

1. **커스텀 노드 설치**
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/HM-RunningHub/ComfyUI_RH_Qwen-Image.git
   cd ComfyUI_RH_Qwen-Image
   pip install -r requirements.txt
   ```

2. **모델 다운로드**
   - 모델이 자동으로 다운로드되거나, 직접 지정한 경로에 배치

3. **ComfyUI 재시작**

### 방법 3: DF11 압축 버전 사용 (메모리 절약)

1. **DF11 노드 설치**
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/verIdyia/ComfyUI-Qwen-Image-DF11.git
   ```

2. **압축 모델 다운로드**
   - DFloat11 압축 버전으로 메모리 사용량 대폭 감소

## 🔧 워크플로우 설정

### 네이티브 워크플로우
- **UNETLoader**: Qwen UNet 모델 로드
- **CLIPLoader**: Qwen CLIP 모델 로드  
- **VAELoader**: Qwen VAE 모델 로드
- **KSampler**: 4 스텝, CFG 3.5 권장

### 커스텀 노드 워크플로우
- **RH_QwenImageLoader**: 통합 모델 로더
- **RH_QwenImageGenerator**: 원스텝 이미지 생성

## ⚙️ 최적 설정값

- **Steps**: 4 (Lightning LoRA 사용)
- **CFG Scale**: 3.5
- **Sampler**: dpmpp_2m
- **Scheduler**: karras
- **Resolution**: 1024x1024 권장

## 🎨 프롬프트 팁

### 텍스트 포함 이미지 생성
```
A beautiful poster with Korean text "안녕하세요", modern design, high quality
```

### 다양한 스타일 지원
```
anime style girl, detailed, colorful
photorealistic portrait, professional lighting
watercolor painting, artistic, soft colors
```

### 복잡한 장면 구성
```
A busy street scene with multiple people, cars, and Korean shop signs, detailed urban environment
```

## 🔍 트러블슈팅

### 메모리 부족 오류
- GGUF 버전 사용
- DF11 압축 버전 사용
- 배치 크기를 1로 설정
- 해상도를 512x512로 낮추기

### 모델 로드 실패
- 모델 파일 경로 확인
- ComfyUI 버전 업데이트
- 필요한 커스텀 노드 설치 확인

### 생성 품질 향상
- 프롬프트 개선 기능 사용
- Negative 프롬프트 활용
- CFG Scale 조정 (2.0-5.0 범위)

## 📚 추가 리소스

- [Qwen-Image 공식 GitHub](https://github.com/QwenLM/Qwen-Image)
- [ComfyUI 공식 문서](https://docs.comfy.org/)
- [Qwen-Image ComfyUI 튜토리얼](https://comfyui-wiki.com/en/tutorial/advanced/image/qwen/qwen-image)

## 🆕 업데이트 기능

현재 워크플로우는 다음 기능들을 지원합니다:

1. **자동 프롬프트 개선**: Ollama의 Qwen 모델을 사용하여 프롬프트 자동 개선
2. **다중 워크플로우 지원**: 네이티브와 커스텀 노드 워크플로우 모두 지원
3. **자동 폴백**: 네이티브 워크플로우 실패시 커스텀 노드로 자동 전환
4. **최적화된 설정**: Qwen-Image에 최적화된 기본 매개변수

Qwen-Image로 놀라운 품질의 이미지를 생성해보세요! 🚀