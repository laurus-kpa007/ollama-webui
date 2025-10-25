# Implementation Guide - Multi-Agent MCP Integration

이 가이드는 Ollama WebUI의 멀티 에이전트 및 MCP 통합 구현을 위한 단계별 지침서입니다.

## 현재 구현 완료 사항

### ✅ Phase 1: Session Management (80% 완료)
- [x] Database schema (User, ChatSession, SessionMetadata, Message, UserPreference)
- [x] SessionManager with optional Redis caching
- [x] Session CRUD API endpoints (`/api/sessions/*`)
- [x] Configuration Manager
- [ ] Session sidebar UI component (다음 단계)

### 📁 구현된 파일 구조

```
ollama-webui/
├── models/
│   ├── __init__.py ✓
│   ├── user.py ✓
│   ├── session.py ✓
│   ├── message.py ✓
│   └── plugin.py ✓
├── services/
│   ├── __init__.py ✓
│   └── session_manager.py ✓
├── utils/
│   ├── __init__.py ✓
│   └── config_manager.py ✓
├── routes/
│   ├── __init__.py ✓
│   └── sessions.py ✓
├── app_new.py ✓ (새로운 애플리케이션 진입점)
├── app_backup.py ✓ (기존 코드 백업)
├── config.json (자동 생성됨)
└── requirements.txt ✓ (업데이트됨)
```

## 다음 단계: 구현 계속하기

### Phase 1 완료: Session Sidebar UI

#### 1. JavaScript 세션 관리 클라이언트 작성

`static/js/session-manager.js` 파일 생성:

```javascript
class SessionManager {
  constructor() {
    this.currentSessionId = null;
    this.sessions = [];
    this.userId = 'default-user'; // 단일 사용자 모드
  }

  async loadSessions() {
    try {
      const response = await fetch(`/api/sessions?user_id=${this.userId}`);
      const data = await response.json();
      this.sessions = data.sessions;
      this.renderSessionList();
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  }

  async createSession(modelName, mode = 'chat') {
    try {
      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          user_id: this.userId,
          model_name: modelName,
          mode: mode
        })
      });
      const data = await response.json();
      this.currentSessionId = data.session.id;
      await this.loadSessions();
      return data.session;
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  }

  async deleteSession(sessionId) {
    if (confirm('이 세션을 삭제하시겠습니까?')) {
      try {
        await fetch(`/api/sessions/${sessionId}`, {method: 'DELETE'});
        await this.loadSessions();
      } catch (error) {
        console.error('Failed to delete session:', error);
      }
    }
  }

  async renameSession(sessionId, newTitle) {
    try {
      await fetch(`/api/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title: newTitle})
      });
      await this.loadSessions();
    } catch (error) {
      console.error('Failed to rename session:', error);
    }
  }

  async togglePin(sessionId) {
    try {
      await fetch(`/api/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({pinned: true}) // API에서 toggle 처리
      });
      await this.loadSessions();
    } catch (error) {
      console.error('Failed to toggle pin:', error);
    }
  }

  renderSessionList() {
    const sidebar = document.getElementById('session-sidebar');
    if (!sidebar) return;

    // 시간별로 그룹화
    const grouped = this.groupSessions(this.sessions);

    let html = '<div class="session-list">';

    for (const [groupName, sessions] of Object.entries(grouped)) {
      if (sessions.length === 0) continue;

      html += `<div class="session-group">
        <h4 class="group-title">${groupName}</h4>`;

      for (const session of sessions) {
        const isActive = session.id === this.currentSessionId;
        html += `
          <div class="session-item ${isActive ? 'active' : ''} ${session.pinned ? 'pinned' : ''}"
               data-session-id="${session.id}">
            <div class="session-icon">
              ${session.mode === 'chat' ? '💬' : '🖼️'}
            </div>
            <div class="session-title" title="${session.title}">
              ${session.title}
            </div>
            <div class="session-actions">
              <button class="btn-pin" onclick="sessionManager.togglePin('${session.id}')">
                ${session.pinned ? '📌' : '📍'}
              </button>
              <button class="btn-delete" onclick="sessionManager.deleteSession('${session.id}')">
                🗑️
              </button>
            </div>
          </div>`;
      }

      html += '</div>';
    }

    html += '</div>';
    sidebar.innerHTML = html;

    // 이벤트 리스너 추가
    document.querySelectorAll('.session-item').forEach(item => {
      item.addEventListener('click', (e) => {
        if (!e.target.closest('.session-actions')) {
          this.loadSession(item.dataset.sessionId);
        }
      });
    });
  }

  groupSessions(sessions) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const last7Days = new Date(today);
    last7Days.setDate(last7Days.getDate() - 7);
    const last30Days = new Date(today);
    last30Days.setDate(last30Days.getDate() - 30);

    const grouped = {
      'Pinned': [],
      'Today': [],
      'Yesterday': [],
      'Previous 7 Days': [],
      'Previous 30 Days': [],
      'Older': []
    };

    for (const session of sessions) {
      const updated = new Date(session.updated_at);

      if (session.pinned) {
        grouped['Pinned'].push(session);
      } else if (updated >= today) {
        grouped['Today'].push(session);
      } else if (updated >= yesterday) {
        grouped['Yesterday'].push(session);
      } else if (updated >= last7Days) {
        grouped['Previous 7 Days'].push(session);
      } else if (updated >= last30Days) {
        grouped['Previous 30 Days'].push(session);
      } else {
        grouped['Older'].push(session);
      }
    }

    return grouped;
  }

  async loadSession(sessionId) {
    try {
      const response = await fetch(`/api/sessions/${sessionId}`);
      const data = await response.json();
      this.currentSessionId = sessionId;
      // 메시지를 채팅 창에 로드
      this.loadMessagesIntoChat(data.messages);
      this.renderSessionList();
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  }

  loadMessagesIntoChat(messages) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    chatMessages.innerHTML = '';
    for (const msg of messages) {
      this.addMessageToChat(msg);
    }
  }

  addMessageToChat(message) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${message.role}`;
    messageDiv.innerHTML = `
      <div class="message-content">${this.formatContent(message.content)}</div>
      ${message.image_url ? `<img src="${message.image_url}" class="message-image">` : ''}
      ${message.agent_name ? `<div class="agent-badge">${message.agent_name}</div>` : ''}
    `;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  formatContent(content) {
    // Simple markdown-like formatting
    return content
      .replace(/\n/g, '<br>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>');
  }
}

// Global instance
const sessionManager = new SessionManager();
```

#### 2. CSS 스타일링

`static/css/sessions.css` 파일 생성:

```css
#session-sidebar {
  width: 260px;
  background: #1a1a1a;
  border-right: 1px solid #333;
  overflow-y: auto;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
}

.session-list {
  padding: 10px;
}

.session-group {
  margin-bottom: 20px;
}

.group-title {
  font-size: 0.85em;
  color: #888;
  text-transform: uppercase;
  margin-bottom: 8px;
  padding-left: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 10px;
  margin-bottom: 5px;
  background: #222;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.session-item:hover {
  background: #2a2a2a;
}

.session-item.active {
  background: #0066cc;
}

.session-item.pinned {
  border-left: 3px solid #ffd700;
}

.session-icon {
  font-size: 1.2em;
  margin-right: 10px;
}

.session-title {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.9em;
}

.session-actions {
  display: flex;
  gap: 5px;
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .session-actions {
  opacity: 1;
}

.session-actions button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1em;
  padding: 2px;
}

.session-actions button:hover {
  transform: scale(1.2);
}
```

#### 3. HTML 통합

`templates/index.html`에 세션 사이드바 추가:

```html
<!-- 기존 body 태그 내부 상단에 추가 -->
<div id="session-sidebar">
  <div class="sidebar-header">
    <h2>Conversations</h2>
    <button id="new-session-btn" onclick="sessionManager.createSession('llama2')">
      ➕ New Chat
    </button>
  </div>
  <!-- 세션 목록이 여기에 동적으로 렌더링됨 -->
</div>

<!-- 기존 채팅 영역을 조정 (왼쪽 여백 추가) -->
<div class="main-content" style="margin-left: 260px;">
  <!-- 기존 채팅 UI -->
</div>

<!-- JS/CSS 추가 -->
<link rel="stylesheet" href="/static/css/sessions.css">
<script src="/static/js/session-manager.js"></script>
<script>
  // 페이지 로드 시 세션 목록 로드
  document.addEventListener('DOMContentLoaded', () => {
    sessionManager.loadSessions();
  });
</script>
```

### Phase 2: MCP Integration

#### 필요한 파일:

1. **`services/mcp_client.py`** - MCP 클라이언트 구현
2. **`services/mcp_server.py`** - MCP 서버 (도구 제공)
3. **`routes/mcp.py`** - MCP API 엔드포인트
4. **Frontend**: 도구 토글 UI

#### 간단한 MCP 서버 예제:

```python
# services/mcp_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ollama-webui-tools")

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

@mcp.tool()
def search_web(query: str) -> dict:
    """Search the web"""
    # 실제 검색 구현
    return {"query": query, "results": []}

if __name__ == "__main__":
    mcp.run()
```

### Phase 3: Autogen Integration

#### 필요한 파일:

1. **`services/autogen_service.py`** - Autogen 에이전트 관리
2. **`routes/autogen.py`** - Autogen API 엔드포인트
3. **Frontend**: 멀티 에이전트 UI 패널

#### Autogen 서비스 예제:

```python
# services/autogen_service.py
from typing import List, Dict
import autogen

class AutogenService:
    def __init__(self, ollama_base_url="http://localhost:11434"):
        self.config_list = [{
            "model": "llama2",
            "api_base": f"{ollama_base_url}/v1",
            "api_key": "ollama"
        }]
        self.agents = {}
        self.create_agents()

    def create_agents(self):
        """Create specialized agents"""
        self.agents['researcher'] = autogen.AssistantAgent(
            name="Researcher",
            llm_config={"config_list": self.config_list},
            system_message="You are a research assistant..."
        )

        self.agents['coder'] = autogen.AssistantAgent(
            name="Coder",
            llm_config={"config_list": self.config_list},
            system_message="You are a senior software engineer..."
        )

        # ... more agents
```

### Phase 4: Plugin System

#### 이미 구현된 부분:
- Configuration Manager ✓

#### 남은 작업:
1. **`plugins/plugin_system.py`** - 플러그인 베이스 클래스 및 매니저
2. **`plugins/example_plugin.py`** - 예제 플러그인
3. **`routes/plugins.py`** - 플러그인 API
4. **Frontend**: 플러그인 관리 UI

자세한 구현은 FEATURE_REQUIREMENTS.md의 리서치 결과를 참조하세요.

## 설치 및 실행

### 1. 의존성 설치

```bash
# 기본 의존성
pip install -r requirements.txt

# PyTorch (GPU 지원 - 선택사항)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Redis (선택사항 - 캐싱용)
# Windows: https://github.com/microsoftarchive/redis/releases
# Linux: sudo apt-get install redis-server
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

### 3. 애플리케이션 실행

```bash
# 새로운 아키텍처로 실행
python app_new.py

# 또는 기존 방식
python app.py
```

### 4. 설정 파일

첫 실행 시 `config.json`이 자동 생성됩니다. 필요에 따라 수정하세요:

```json
{
  "app": {
    "name": "Ollama WebUI",
    "version": "2.0.0",
    "host": "0.0.0.0",
    "port": 5000
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
    "enabled": false
  },
  "mcp": {
    "enabled": false
  }
}
```

## API 문서

### Session Management API

#### GET `/api/sessions`
세션 목록 조회

**Query Parameters:**
- `user_id` (optional): 사용자 ID
- `archived` (optional): 보관된 세션 포함 여부

**Response:**
```json
{
  "sessions": [
    {
      "id": "uuid",
      "title": "Chat - 2025-01-15",
      "model_name": "llama2",
      "mode": "chat",
      "created_at": "2025-01-15T10:00:00",
      "updated_at": "2025-01-15T11:30:00",
      "message_count": 10,
      "pinned": false,
      "archived": false
    }
  ]
}
```

#### POST `/api/sessions`
새 세션 생성

**Request Body:**
```json
{
  "model_name": "llama2",
  "mode": "chat",
  "title": "My Custom Chat"
}
```

#### GET `/api/sessions/{session_id}`
세션 상세 정보 및 메시지 조회

#### PATCH `/api/sessions/{session_id}`
세션 업데이트 (제목 변경, 핀/보관)

**Request Body:**
```json
{
  "title": "New Title",
  "pinned": true,
  "archived": false
}
```

#### DELETE `/api/sessions/{session_id}`
세션 삭제

#### POST `/api/sessions/{session_id}/messages`
메시지 추가

**Request Body:**
```json
{
  "role": "user",
  "content": "Hello, how are you?",
  "image_url": "/static/uploads/image.png",
  "agent_name": "researcher"
}
```

## 디버깅 팁

### 데이터베이스 확인

```bash
# SQLite DB 확인
sqlite3 app.db
.tables
.schema chat_sessions
SELECT * FROM chat_sessions;
```

### Redis 확인

```bash
redis-cli
> KEYS session:*
> GET session:{uuid}
```

### 로그 확인

```python
# app_new.py에서 로깅 활성화
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 다음 단계 권장사항

1. **Phase 1 완료**: 세션 사이드바 UI 구현 (위 가이드 참조)
2. **Phase 2 시작**: MCP 클라이언트/서버 구현
3. **Phase 3**: Autogen 멀티 에이전트 통합
4. **Phase 4**: 플러그인 시스템 완성
5. **테스트 및 문서화**

## 참고 자료

- [Flask-SQLAlchemy 문서](https://flask-sqlalchemy.palletsprojects.com/)
- [AutoGen 문서](https://microsoft.github.io/autogen/)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Redis Python Client](https://redis-py.readthedocs.io/)

## 기여

버그 리포트나 기능 제안은 GitHub Issues에 올려주세요.

## 라이센스

MIT License
