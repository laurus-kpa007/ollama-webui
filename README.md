# Ollama WebUI

Ollama를 위한 웹 기반 채팅 인터페이스입니다. 다중 사용자 환경에서 동시 접속을 지원하며, 여러 AI 모델과의 채팅 및 이미지 분석 기능을 제공합니다.

## 주요 특징

- 🤖 **다중 모델 지원**: Ollama에서 사용 가능한 모든 모델 선택 가능
- 💬 **실시간 스트리밍**: 스트림 모드로 실시간 응답 확인
- 🖼️ **이미지 분석**: 비전 모델을 통한 이미지 분석 (llava 등)
- 🎨 **이미지 생성**: Stable Diffusion을 통한 텍스트-이미지 생성
- 🖼️ **이미지 변환**: img2img를 통한 이미지-이미지 변환
- 👥 **다중 사용자**: 동시에 여러 사용자가 다른 모델 사용 가능
- 📱 **반응형 디자인**: 모바일 및 데스크톱 지원
- ⚡ **고성능**: Ollama의 우수한 동시 처리 능력 활용

## 사전 요구사항

- Python 3.8+
- Ollama가 설치되고 실행 중이어야 함
- (선택사항) 이미지 생성을 위한 Automatic1111 WebUI

### Ollama 설치 및 설정

1. [Ollama](https://ollama.ai) 설치
2. 모델 다운로드:
```bash
ollama pull llama2
ollama pull llava  # 이미지 분석용
```
3. Ollama 서버 실행 (기본 포트: 11434)

### Stable Diffusion WebUI 설치 및 설정 (이미지 생성용)

1. [Automatic1111 WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) 설치
2. API 모드로 실행:
```bash
./webui.sh --api
# 또는 Windows의 경우
./webui-user.bat --api
```
3. WebUI가 실행되면 기본적으로 포트 7860에서 API 사용 가능

## 설치 및 실행

1. **프로젝트 클론**
```bash
git clone <repository-url>
cd ollama-webui
```

2. **가상 환경 생성 및 활성화**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows
```

3. **의존성 설치**
```bash
pip install -r requirements.txt
```

4. **환경 설정**
```bash
cp .env.example .env
# .env 파일 편집하여 필요한 설정 조정
```

5. **애플리케이션 실행**
```bash
python app.py
```

6. **웹 브라우저에서 접속**
```
http://localhost:5000
```

## 설정 옵션

### 환경 변수 (.env 파일)

- `OLLAMA_HOST`: Ollama 서버 호스트 (기본값: localhost)
- `OLLAMA_PORT`: Ollama 서버 포트 (기본값: 11434)
- `SD_HOST`: Stable Diffusion WebUI 호스트 (기본값: localhost)
- `SD_PORT`: Stable Diffusion WebUI 포트 (기본값: 7860)
- `FLASK_HOST`: Flask 서버 호스트 (기본값: 0.0.0.0)
- `FLASK_PORT`: Flask 서버 포트 (기본값: 5000)
- `FLASK_DEBUG`: 디버그 모드 (기본값: False)

### 채팅 설정

- **Temperature**: 0.0-2.0 범위의 창의성 조절 (낮을수록 일관성 높음)
- **Max Tokens**: 최대 응답 길이 제한
- **Stream Mode**: 실시간 스트리밍 응답 활성화/비활성화

### 이미지 생성 설정

- **Image Size**: 생성할 이미지 크기 (512x512, 768x768, 1024x1024 등)
- **Sampling Steps**: 샘플링 단계 수 (10-50, 높을수록 품질 향상)
- **CFG Scale**: 프롬프트 준수도 (1-20, 높을수록 프롬프트 충실)
- **Negative Prompt**: 생성하지 않을 내용 지정
- **Denoising Strength**: img2img 변환 강도 (0.1-1.0)

## 사용법

### 채팅 모드
1. **모델 선택**: 좌측 사이드바에서 사용할 AI 모델 선택
2. **채팅**: 하단 입력창에 메시지 입력 후 전송
3. **이미지 분석**: 이미지 업로드 후 메시지 전송 (llava 등 비전 모델 필요)

### 이미지 생성 모드
1. **모드 변경**: 사이드바에서 "🎨 이미지 생성" 선택
2. **설정 조정**: 이미지 크기, 샘플링 스텝, CFG Scale 등 조정
3. **프롬프트 입력**: 생성할 이미지 설명 입력
4. **네거티브 프롬프트**: (선택사항) 피하고 싶은 내용 입력
5. **생성**: 전송 버튼 클릭하여 이미지 생성

### 이미지 변환 모드 (img2img)
1. **모드 변경**: 사이드바에서 "🖼️ 이미지 변환" 선택
2. **이미지 업로드**: 변환할 기본 이미지 업로드
3. **설정 조정**: 디노이징 강도 등 조정
4. **프롬프트 입력**: 변환할 내용 설명 입력
5. **변환**: 전송 버튼 클릭하여 이미지 변환

## API 엔드포인트

### Ollama 관련
- `GET /api/models`: 사용 가능한 채팅 모델 목록 조회
- `POST /api/chat`: 채팅 메시지 전송 (스트림/일반 모드)
- `POST /api/analyze_image`: 이미지 분석 (llava 등)

### Stable Diffusion 관련
- `GET /api/sd_models`: 사용 가능한 이미지 생성 모델 목록 조회
- `POST /api/generate_image`: 텍스트-이미지 생성 (txt2img)
- `POST /api/img2img`: 이미지-이미지 변환

### 기타
- `POST /api/upload`: 이미지 파일 업로드

## 이전 LM Studio 버전과의 차이점

### 장점
- ✅ **동시 다중 모델 지원**: 사용자별로 다른 모델 사용 가능
- ✅ **더 나은 동시 처리**: Ollama의 우수한 멀티 스레딩 지원
- ✅ **모델 관리 편의성**: 모델 다운로드/관리가 더 간편
- ✅ **메모리 효율성**: 더 효율적인 모델 로딩/언로딩

### 주의사항
- 📋 **API 호환성**: OpenAI API와 유사하지만 일부 차이점 존재
- 🔧 **설정**: Ollama 서버가 별도로 실행되어야 함

## 트러블슈팅

### 연결 문제
- Ollama 서버가 실행 중인지 확인
- 포트 설정 확인 (기본: 11434)
- 방화벽 설정 확인

### 모델 문제
- `ollama list` 명령으로 설치된 모델 확인
- 필요한 모델이 없다면 `ollama pull <model-name>`으로 다운로드

### 이미지 분석 문제
- llava 등 비전 모델이 설치되어 있는지 확인
- 지원되는 이미지 형식: PNG, JPG, JPEG, GIF, BMP, WebP

## 라이선스

MIT License

## 기여

버그 리포트나 기능 요청은 Issues를 통해 제출해 주세요.