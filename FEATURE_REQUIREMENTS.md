# Feature Requirements

## 추가 기능 요청사항

### 1. 세션별 채팅 히스토리 관리 기능
- 각 대화 세션을 독립적으로 관리
- 세션 목록 표시 및 선택 기능
- 세션별 대화 내용 저장 및 불러오기
- 세션 삭제 및 이름 변경 기능

### 2. Autogen 기반 에이전트 시스템
- Ollama 기본 인터페이스를 Autogen 에이전트로 전환
- MCP (Model Context Protocol) 통합
- 에이전트 설정을 환경설정에 추가
- MCP 서버 연결 설정을 환경설정에 추가

### 3. 대화창 내 Agent/MCP 토글 기능
- Claude App과 유사한 UI/UX
- 대화창에서 실시간으로 Agent 활성화/비활성화
- 대화창에서 실시간으로 MCP 활성화/비활성화
- 토글 상태 시각적 표시

### 4. 확장 가능한 아키텍처 설계
- 향후 기능 추가를 고려한 모듈화
- 플러그인 시스템 구조
- 설정 관리 체계화
- API 엔드포인트 표준화

## 구현 우선순위
1. 아키텍처 재설계 (확장성 기반)
2. 세션 관리 시스템
3. Autogen 에이전트 통합
4. MCP 통합
5. UI/UX 개선 (토글 기능)

## 기술 스택 고려사항
- Backend: Flask (현재) → 유지 또는 FastAPI로 전환 검토
- Agent Framework: Autogen
- Protocol: MCP (Model Context Protocol)
- Database: SQLite 또는 PostgreSQL (세션 저장용)
- Frontend: 현재 바닐라 JS → 유지 또는 React/Vue 검토
