# Ollama WebUI v2.0 - Multi-Agent AI Platform

완전한 멀티 에이전트 AI 플랫폼으로 확장된 Ollama WebUI입니다.

## 🎯 새로운 기능

### ✅ Phase 1: 세션 관리 시스템
- **세션별 채팅 히스토리**: 각 대화를 독립적으로 관리
- **시간순 그룹화**: Today, Yesterday, Previous 7 Days 등으로 자동 분류
- **검색 기능**: 세션 제목 및 내용 전체 검색
- **세션 작업**: 핀, 보관, 이름 변경, 삭제
- **자동 제목 생성**: 첫 메시지로부터 자동으로 제목 생성

### ✅ Phase 2: MCP (Model Context Protocol) 통합
- **17개 이상의 도구**:
  - 수학: add_numbers, multiply_numbers, calculate
  - 텍스트: count_words, count_characters, reverse_text, to_uppercase, to_lowercase
  - 날짜/시간: get_current_time, get_current_date, get_day_of_week
  - 파일: list_files, read_file
  - 웹: fetch_url, search_web
  - 이미지: generate_image_with_comfyui
- **도구 카테고리**: Math, Text, Date/Time, Files, Web, Image
- **도구 테스트**: 각 도구를 직접 테스트할 수 있는 인터페이스
- **세션별 도구 활성화**: 각 세션마다 다른 도구 조합 사용 가능

### ✅ Phase 3: Autogen 멀티 에이전트 시스템
- **6개의 전문 에이전트**:
  - **Researcher**: 연구 및 정보 수집
  - **Coder**: 코드 작성 및 디버깅
  - **Creative**: 창의적 아이디어 생성
  - **ImageSpecialist**: 이미지 프롬프트 최적화
  - **Critic**: 품질 검토 및 피드백
  - **Planner**: 작업 계획 및 조율
- **워크플로우**:
  - Sequential: 에이전트가 순차적으로 작업
  - Group Chat: 에이전트들이 협업하여 토론
  - Image Enhancement: 이미지 프롬프트 개선 전용 워크플로우
- **에이전트 선택**: 작업에 필요한 에이전트만 선택하여 실행

### ✅ Phase 4: 플러그인 시스템
- **플러그인 프레임워크**: 확장 가능한 플러그인 아키텍처
- **플러그인 발견**: 자동으로 plugins/ 디렉토리에서 플러그인 검색
- **라이프사이클 관리**: 플러그인 활성화/비활성화
- **훅 시스템**: on_message, on_response 훅으로 메시지 처리
- **라우트 등록**: 플러그인이 자체 API 엔드포인트 추가 가능
- **예제 플러그인**: 플러그인 개발을 위한 템플릿 제공

## 🚀 시작하기

### 1. 의존성 설치

```bash
# 기본 의존성
pip install -r requirements.txt

# PyTorch (선택사항 - GPU 지원)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

### 2. 데이터베이스 초기화

```bash
python
>>> from app_new import create_app
>>> app = create_app()
>>> with app.app_context():
...     from models import db
...     db.create_all()
>>> exit()
```

### 3. 서버 실행

```bash
# 새 버전 (권장)
python app_new.py

# 또는 기존 버전
python app.py
```

### 4. 브라우저에서 접속

```
http://localhost:5000
```

새로운 UI는 `http://localhost:5000` (app_new.py 사용 시)에서 확인하거나,
`templates/index.html`을 `templates/index_new.html`로 교체하세요.

## 📖 사용 가이드

### 세션 관리

1. **새 채팅 시작**: 사이드바의 "New Chat" 버튼 클릭
2. **세션 전환**: 사이드바에서 원하는 세션 클릭
3. **세션 작업**: 세션에 마우스 오버하여 핀/삭제 버튼 표시
4. **컨텍스트 메뉴**: 세션의 ⋮ 버튼으로 이름 변경, 보관, 삭제
5. **검색**: 상단 검색창으로 세션 검색

### MCP 도구 사용

1. **도구 탭**: 상단의 "🔧 Tools" 탭 클릭
2. **연결**: "Connect" 버튼으로 MCP 서버 연결
3. **도구 선택**: 사용할 도구의 토글 스위치 활성화
4. **도구 테스트**: 각 도구의 "Test Tool" 버튼으로 직접 테스트
5. **채팅에서 사용**: 활성화된 도구는 AI가 자동으로 사용 가능

### 멀티 에이전트 사용

1. **에이전트 탭**: 상단의 "🤖 Agents" 탭 클릭
2. **워크플로우 선택**: 사전 정의된 워크플로우 선택 (또는 직접 에이전트 선택)
3. **작업 입력**: "Task Description"에 작업 설명 입력
4. **모드 선택**: Sequential 또는 Group Chat 선택
5. **실행**: "Run Agent Task" 버튼 클릭
6. **결과 확인**: 에이전트 대화 및 최종 결과 확인

## 📁 프로젝트 구조

```
ollama-webui/
├── app.py                          # 기존 버전
├── app_new.py                      # 새 버전 (모든 기능 포함)
├── app_backup.py                   # 백업
├── config.json                     # 설정 파일 (자동 생성)
│
├── models/                         # 데이터베이스 모델
│   ├── user.py                     # 사용자
│   ├── session.py                  # 세션 및 메타데이터
│   ├── message.py                  # 메시지
│   └── plugin.py                   # 사용자 환경설정
│
├── services/                       # 비즈니스 로직
│   ├── session_manager.py          # 세션 관리
│   ├── mcp_server.py               # MCP 도구 서버
│   ├── mcp_client.py               # MCP 클라이언트
│   └── autogen_service.py          # Autogen 멀티 에이전트
│
├── routes/                         # API 엔드포인트
│   ├── sessions.py                 # 세션 API
│   ├── mcp.py                      # MCP API
│   ├── autogen.py                  # Autogen API
│   └── plugins.py                  # 플러그인 API
│
├── plugins/                        # 플러그인 디렉토리
│   ├── plugin_system.py            # 플러그인 프레임워크
│   └── example_plugin.py           # 예제 플러그인
│
├── utils/                          # 유틸리티
│   └── config_manager.py           # 설정 관리
│
├── static/
│   ├── js/
│   │   ├── session-manager.js      # 세션 UI
│   │   ├── mcp-manager.js          # 도구 UI
│   │   ├── autogen-manager.js      # 에이전트 UI
│   │   └── app.js                  # 메인 앱 로직
│   └── css/
│       ├── sessions.css            # 세션 스타일
│       ├── mcp-tools.css           # 도구 스타일
│       └── style.css               # 메인 스타일
│
└── templates/
    ├── index.html                  # 기존 HTML
    └── index_new.html              # 새 HTML (4-탭 인터페이스)
```

## 🔌 API 엔드포인트

### 세션 관리
- `GET /api/sessions` - 세션 목록
- `POST /api/sessions` - 새 세션 생성
- `GET /api/sessions/<id>` - 세션 상세
- `PATCH /api/sessions/<id>` - 세션 업데이트
- `DELETE /api/sessions/<id>` - 세션 삭제
- `POST /api/sessions/<id>/messages` - 메시지 추가
- `GET /api/sessions/search` - 세션 검색

### MCP 도구
- `POST /api/mcp/connect` - MCP 서버 연결
- `GET /api/mcp/tools` - 도구 목록
- `POST /api/mcp/tools/<name>/call` - 도구 실행
- `GET /api/mcp/status` - 연결 상태
- `POST /api/mcp/test` - 도구 테스트

### Autogen 에이전트
- `GET /api/autogen/agents` - 에이전트 목록
- `POST /api/autogen/task/sequential` - 순차 작업
- `POST /api/autogen/task/group` - 그룹 작업
- `POST /api/autogen/image/enhance` - 이미지 프롬프트 개선
- `GET /api/autogen/workflows` - 워크플로우 목록
- `POST /api/autogen/test` - 에이전트 테스트

### 플러그인
- `GET /api/plugins` - 플러그인 목록
- `POST /api/plugins/discover` - 플러그인 발견
- `POST /api/plugins/<name>/enable` - 플러그인 활성화
- `POST /api/plugins/<name>/disable` - 플러그인 비활성화
- `GET /api/plugins/<name>` - 플러그인 정보

## ⚙️ 설정

`config.json` 파일을 편집하여 설정을 변경할 수 있습니다:

```json
{
  "app": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false
  },
  "database": {
    "uri": "sqlite:///app.db"
  },
  "redis": {
    "enabled": false,
    "host": "localhost",
    "port": 6379
  },
  "ollama": {
    "host": "localhost",
    "port": 11434
  },
  "autogen": {
    "enabled": true
  },
  "mcp": {
    "enabled": true
  },
  "plugins": {
    "enabled": ["example_plugin"]
  }
}
```

## 🧩 플러그인 개발

플러그인을 만들려면:

1. `plugins/` 디렉토리에 새 파일 생성 (예: `my_plugin.py`)
2. `PluginBase`를 상속하는 클래스 작성:

```python
from plugin_system import PluginBase

class MyPlugin(PluginBase):
    name = "My Plugin"
    version = "1.0.0"
    description = "Description of my plugin"
    author = "Your Name"

    def initialize(self) -> bool:
        # 초기화 로직
        return True

    def cleanup(self):
        # 정리 로직
        pass

    def on_message(self, message):
        # 메시지 처리
        return message
```

3. `config.json`의 `plugins.enabled`에 플러그인 이름 추가
4. 서버 재시작

## 🧪 테스트

### MCP 도구 테스트
```bash
# MCP 서버 직접 실행
python services/mcp_server.py

# MCP 클라이언트 테스트
python services/mcp_client.py
```

### Autogen 에이전트 테스트
```python
from services.autogen_service import get_autogen_service

service = get_autogen_service()
result = service.sequential_task(
    "Python의 장점은 무엇인가요?",
    ['researcher', 'critic']
)
print(result)
```

### API 테스트
```bash
# 세션 생성
curl -X POST http://localhost:5000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"model_name": "llama2", "mode": "chat"}'

# MCP 도구 호출
curl -X POST http://localhost:5000/api/mcp/tools/add_numbers/call \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"a": 5, "b": 3}}'

# 에이전트 작업
curl -X POST http://localhost:5000/api/autogen/task/sequential \
  -H "Content-Type: application/json" \
  -d '{"task": "Explain Python", "agents": ["researcher"]}'
```

## 📚 문서

- **[FEATURE_REQUIREMENTS.md](FEATURE_REQUIREMENTS.md)**: 전체 기능 명세 및 리서치
- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)**: 단계별 구현 가이드
- **[PROGRESS_SUMMARY.md](PROGRESS_SUMMARY.md)**: 진행 상황 요약

## 🔍 주요 특징

### 확장 가능한 아키텍처
- 모듈화된 구조로 새 기능 추가 용이
- Blueprint 기반 라우팅
- 플러그인 시스템으로 무한 확장

### 다양한 AI 모델 지원
- Ollama (LLM)
- ComfyUI (이미지 생성)
- Qwen (멀티모달)
- Autogen (멀티 에이전트)

### 유연한 도구 시스템
- MCP 표준 프로토콜 사용
- 쉬운 도구 추가
- 세션별 도구 커스터마이징

### 협업 AI
- 여러 AI 에이전트가 협업
- 각 에이전트의 전문 분야 활용
- 복잡한 작업을 단계별로 처리

## 🛠️ 문제 해결

### Redis 연결 실패
Redis는 선택사항입니다. `config.json`에서 비활성화:
```json
{"redis": {"enabled": false}}
```

### MCP 서버 연결 안됨
1. MCP 서버가 실행 중인지 확인
2. `services/mcp_server.py` 경로가 올바른지 확인
3. Python 경로 문제 시 절대 경로 사용

### Autogen 에러
1. `pyautogen` 패키지 설치 확인: `pip install pyautogen`
2. Ollama가 실행 중인지 확인
3. 모델이 다운로드되어 있는지 확인: `ollama list`

### 데이터베이스 에러
데이터베이스 재생성:
```bash
rm app.db
python
>>> from app_new import create_app
>>> app = create_app()
>>> with app.app_context():
...     from models import db
...     db.create_all()
```

## 🤝 기여

버그 리포트나 기능 제안은 GitHub Issues에 올려주세요.

## 📄 라이선스

MIT License

## 🎉 크레딧

- **Ollama**: LLM 백엔드
- **ComfyUI**: 이미지 생성
- **Microsoft AutoGen**: 멀티 에이전트 프레임워크
- **MCP**: Model Context Protocol

---

**Ollama WebUI v2.0** - Powered by Multi-Agent AI 🚀
