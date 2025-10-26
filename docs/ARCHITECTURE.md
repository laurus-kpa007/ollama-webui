# System Architecture Documentation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagrams](#architecture-diagrams)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Sequence Diagrams](#sequence-diagrams)
6. [Database Schema](#database-schema)
7. [API Reference](#api-reference)
8. [Technology Stack](#technology-stack)

---

## 🎯 System Overview

Ollama WebUI v2.0 is a multi-layered, extensible AI platform that integrates:
- **Session Management**: Persistent conversation history
- **MCP Tools**: Model Context Protocol for tool integration
- **Multi-Agent AI**: Specialized AI agents working collaboratively
- **Plugin System**: Extensible architecture for custom features

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Browser (HTML/CSS/JavaScript)                            │  │
│  │  - Session UI (session-manager.js)                       │  │
│  │  - MCP Tools UI (mcp-manager.js)                         │  │
│  │  - Agent UI (autogen-manager.js)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST API
┌───────────────────────────▼─────────────────────────────────────┐
│                    Application Layer (Flask)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Sessions   │  │     MCP     │  │ Autogen  │  │ Plugins  │ │
│  │  Blueprint  │  │  Blueprint  │  │Blueprint │  │Blueprint │ │
│  └─────────────┘  └─────────────┘  └──────────┘  └──────────┘ │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      Service Layer                               │
│  ┌────────────────┐  ┌─────────────┐  ┌──────────────────────┐ │
│  │SessionManager  │  │ MCP Client  │  │ AutogenService       │ │
│  │                │  │ MCP Server  │  │ (6 Agents)           │ │
│  └────────────────┘  └─────────────┘  └──────────────────────┘ │
│  ┌────────────────┐  ┌─────────────┐  ┌──────────────────────┐ │
│  │PluginManager   │  │ConfigManager│  │ OllamaClient         │ │
│  └────────────────┘  └─────────────┘  └──────────────────────┘ │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                       Data Layer                                 │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────────────────┐  │
│  │  PostgreSQL  │  │  Redis   │  │    File Storage          │  │
│  │  (Sessions)  │  │ (Cache)  │  │    (Uploads/Config)      │  │
│  └──────────────┘  └──────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    External Services                             │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────────────────┐  │
│  │   Ollama     │  │ ComfyUI  │  │    MCP Tools             │  │
│  │   (LLM)      │  │ (Images) │  │    (17+ tools)           │  │
│  └──────────────┘  └──────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Architecture Diagrams

### 1. Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation Layer                                          │
│  - HTML Templates (index_new.html)                          │
│  - CSS Styles (sessions.css, mcp-tools.css)                 │
│  - JavaScript Managers (session, mcp, autogen)              │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│  API Layer (Flask Blueprints)                               │
│  - /api/sessions/*     (Session Management)                 │
│  - /api/mcp/*          (Tool Operations)                    │
│  - /api/autogen/*      (Agent Operations)                   │
│  - /api/plugins/*      (Plugin Management)                  │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│  Business Logic Layer (Services)                            │
│  - SessionManager      (CRUD + Search)                      │
│  - MCPClient/Server    (Tool Discovery & Execution)         │
│  - AutogenService      (Multi-Agent Orchestration)          │
│  - PluginManager       (Plugin Lifecycle)                   │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│  Data Access Layer (Models)                                 │
│  - User, ChatSession, Message                               │
│  - SessionMetadata, UserPreference                          │
│  - SQLAlchemy ORM                                           │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│  Data Storage Layer                                          │
│  - SQLite/PostgreSQL (Primary DB)                           │
│  - Redis (Optional Cache)                                   │
│  - File System (Uploads, Config)                            │
└─────────────────────────────────────────────────────────────┘
```

### 2. Component Interaction Diagram

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────────────────────────────────────────────┐
│                    Flask App                            │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Session  │  │   MCP    │  │ Autogen  │            │
│  │Blueprint │  │Blueprint │  │Blueprint │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
│       │             │              │                   │
│       ▼             ▼              ▼                   │
│  ┌─────────────────────────────────────────┐          │
│  │        Service Layer                     │          │
│  │                                          │          │
│  │  SessionManager ← → PluginManager       │          │
│  │       ↓                    ↓             │          │
│  │  MCPClient    ← → AutogenService        │          │
│  │       ↓                    ↓             │          │
│  └───────┼────────────────────┼─────────────┘          │
│          │                    │                        │
└──────────┼────────────────────┼────────────────────────┘
           │                    │
           ▼                    ▼
    ┌───────────┐        ┌──────────┐
    │ Database  │        │  Ollama  │
    │ (SQLite)  │        │  Server  │
    └───────────┘        └──────────┘
```

---

## 🔧 Component Details

### 1. Session Management System

**Purpose**: Manage conversation history with persistence and search

**Components**:
- `SessionManager` (services/session_manager.py)
- `Session Blueprint` (routes/sessions.py)
- `Database Models` (models/session.py, models/message.py)
- `Session UI` (static/js/session-manager.js)

**Key Features**:
- Create/Read/Update/Delete sessions
- Time-based grouping (Today, Yesterday, etc.)
- Full-text search across sessions and messages
- Pin/Archive/Rename operations
- Redis caching for performance

**Storage**:
```
ChatSession (table)
├── id (PK)
├── user_id (FK)
├── title
├── model_name
├── mode
├── created_at
├── updated_at
├── archived
└── pinned

Message (table)
├── id (PK)
├── session_id (FK)
├── role (user/assistant/system)
├── content
├── image_url
├── tool_calls (JSON)
├── agent_name
└── created_at
```

### 2. MCP (Model Context Protocol) System

**Purpose**: Provide reusable tools for AI agents

**Components**:
- `MCP Server` (services/mcp_server.py) - 17+ tools
- `MCP Client` (services/mcp_client.py) - Tool discovery & execution
- `MCP Blueprint` (routes/mcp.py) - API endpoints
- `MCP UI` (static/js/mcp-manager.js) - Tool management interface

**Available Tools**:
- **Math**: add_numbers, multiply_numbers, calculate
- **Text**: count_words, count_characters, reverse_text, to_uppercase, to_lowercase
- **Date/Time**: get_current_time, get_current_date, get_day_of_week
- **Files**: list_files, read_file
- **Web**: fetch_url, search_web
- **Image**: generate_image_with_comfyui

**Architecture**:
```
MCP Client (Web UI)
      ↓ HTTP
MCP API (Flask)
      ↓ Async calls
MCP Client (Python)
      ↓ stdio/HTTP
MCP Server (Python)
      ↓ Tool execution
Result ← Return
```

### 3. Autogen Multi-Agent System

**Purpose**: Coordinate multiple specialized AI agents

**Components**:
- `AutogenService` (services/autogen_service.py)
- `6 Specialized Agents`:
  - **Researcher**: Information gathering & analysis
  - **Coder**: Code generation & debugging
  - **Creative**: Creative ideation & content
  - **ImageSpecialist**: Image prompt optimization
  - **Critic**: Quality review & feedback
  - **Planner**: Task planning & coordination

**Workflows**:
1. **Sequential**: Agents work one after another
2. **Group Chat**: Agents collaborate in discussion
3. **Image Enhancement**: Specialized image workflow

**Agent Interaction**:
```
User Task
    ↓
AutogenService
    ↓
┌───────────────────────────────┐
│  Sequential Workflow          │
│  Agent1 → Agent2 → Agent3     │
└───────────────────────────────┘
         OR
┌───────────────────────────────┐
│  Group Chat Workflow          │
│  Agent1 ↔ Agent2 ↔ Agent3    │
│     ↕       ↕       ↕         │
│    Manager coordinates        │
└───────────────────────────────┘
    ↓
Result
```

### 4. Plugin System

**Purpose**: Extend functionality without modifying core code

**Components**:
- `PluginBase` (plugins/plugin_system.py) - Abstract base class
- `PluginManager` (plugins/plugin_system.py) - Lifecycle management
- `Plugin Blueprint` (routes/plugins.py) - API endpoints

**Plugin Lifecycle**:
```
1. Discovery
   PluginManager scans plugins/ directory

2. Loading
   Import module and instantiate plugin class

3. Initialization
   Call plugin.initialize()

4. Hook Registration
   Register on_message, on_response hooks

5. Route Registration
   Add plugin routes to Flask app

6. Execution
   Call hooks when events occur

7. Cleanup
   Call plugin.cleanup() on disable
```

**Plugin Capabilities**:
- Add custom routes
- Hook into message flow
- Store configuration
- Add UI elements

---

## 📊 Data Flow

### 1. Chat Message Flow

```
User Input (Browser)
       ↓
JavaScript sends POST /api/chat
       ↓
Flask Route Handler
       ↓
┌──────────────────────────────┐
│ Plugin Hook: on_message()    │
│ - Modify message             │
│ - Add metadata               │
└──────────────────────────────┘
       ↓
Save to SessionManager
       ↓
Send to Ollama API
       ↓
Receive Response
       ↓
┌──────────────────────────────┐
│ Plugin Hook: on_response()   │
│ - Modify response            │
│ - Add processing             │
└──────────────────────────────┘
       ↓
Save Response to SessionManager
       ↓
Return to Browser
       ↓
Display in Chat UI
```

### 2. MCP Tool Execution Flow

```
User Enables Tool (UI)
       ↓
POST /api/mcp/session/{id}/tools
       ↓
Update SessionMetadata.enabled_tools
       ↓
User Sends Chat Message
       ↓
AI Agent decides to use tool
       ↓
POST /api/mcp/tools/{name}/call
       ↓
MCPClient.call_tool()
       ↓
MCP Server executes tool
       ↓
Return Result
       ↓
AI Agent uses result in response
       ↓
Response with tool metadata saved
```

### 3. Multi-Agent Workflow

```
User submits task
       ↓
POST /api/autogen/task/sequential
       ↓
AutogenService.sequential_task()
       ↓
┌─────────────────────────────────┐
│ Agent 1 (Researcher)            │
│ - Analyze task                  │
│ - Gather information            │
│ - Output: Research findings     │
└─────────────────────────────────┘
       ↓ Pass result
┌─────────────────────────────────┐
│ Agent 2 (Coder)                 │
│ - Review research               │
│ - Generate code                 │
│ - Output: Code solution         │
└─────────────────────────────────┘
       ↓ Pass result
┌─────────────────────────────────┐
│ Agent 3 (Critic)                │
│ - Review code                   │
│ - Provide feedback              │
│ - Output: Final recommendations │
└─────────────────────────────────┘
       ↓
Aggregate Results
       ↓
Return conversation history + final result
```

### 4. Session Creation & Management

```
User clicks "New Chat"
       ↓
POST /api/sessions
{
  user_id: "default-user",
  model_name: "llama2",
  mode: "chat"
}
       ↓
SessionManager.create_session()
       ↓
┌─────────────────────────────────┐
│ 1. Create ChatSession           │
│    - Generate UUID              │
│    - Set default title          │
│    - Set timestamps             │
├─────────────────────────────────┤
│ 2. Create SessionMetadata       │
│    - Set default temperature    │
│    - Initialize empty arrays    │
├─────────────────────────────────┤
│ 3. Save to Database             │
│    - db.session.add()           │
│    - db.session.commit()        │
├─────────────────────────────────┤
│ 4. Cache in Redis (optional)    │
│    - redis.setex()              │
└─────────────────────────────────┘
       ↓
Return session object
       ↓
Update UI sidebar
```

---

## 📈 Sequence Diagrams

### Sequence 1: Session-Based Chat

```
User          Browser       Flask App    SessionMgr   Ollama      Database
 │                │             │            │           │            │
 │ Type msg       │             │            │           │            │
 │───────────────>│             │            │           │            │
 │                │             │            │           │            │
 │                │ POST /api/chat           │           │            │
 │                │────────────>│            │           │            │
 │                │             │            │           │            │
 │                │             │ save_message(user)     │            │
 │                │             │───────────>│           │            │
 │                │             │            │           │            │
 │                │             │            │ INSERT    │            │
 │                │             │            │──────────────────────>│
 │                │             │            │           │            │
 │                │             │ POST /v1/chat          │            │
 │                │             │───────────────────────>│            │
 │                │             │            │           │            │
 │                │             │ Stream response        │            │
 │                │             │<───────────────────────│            │
 │                │             │            │           │            │
 │                │ SSE stream  │            │           │            │
 │                │<────────────│            │           │            │
 │                │             │            │           │            │
 │ Display        │             │            │           │            │
 │<───────────────│             │            │           │            │
 │                │             │            │           │            │
 │                │             │ save_message(assistant)│            │
 │                │             │───────────>│           │            │
 │                │             │            │           │            │
 │                │             │            │ INSERT    │            │
 │                │             │            │──────────────────────>│
 │                │             │            │           │            │
```

### Sequence 2: MCP Tool Usage

```
User       Browser      Flask       MCPClient    MCPServer    Tool
 │            │           │             │            │          │
 │ Enable     │           │             │            │          │
 │  Tool      │           │             │            │          │
 │───────────>│           │             │            │          │
 │            │           │             │            │          │
 │            │ PATCH /api/mcp/session/{id}/tools   │          │
 │            │──────────>│             │            │          │
 │            │           │             │            │          │
 │            │ OK        │             │            │          │
 │            │<──────────│             │            │          │
 │            │           │             │            │          │
 │ Call Tool  │           │             │            │          │
 │───────────>│           │             │            │          │
 │            │           │             │            │          │
 │            │ POST /api/mcp/tools/{name}/call     │          │
 │            │──────────>│             │            │          │
 │            │           │             │            │          │
 │            │           │ call_tool() │            │          │
 │            │           │────────────>│            │          │
 │            │           │             │            │          │
 │            │           │             │ execute()  │          │
 │            │           │             │───────────>│          │
 │            │           │             │            │          │
 │            │           │             │            │ run()    │
 │            │           │             │            │─────────>│
 │            │           │             │            │          │
 │            │           │             │            │ result   │
 │            │           │             │            │<─────────│
 │            │           │             │            │          │
 │            │           │             │ result     │          │
 │            │           │             │<───────────│          │
 │            │           │             │            │          │
 │            │           │ result      │            │          │
 │            │           │<────────────│            │          │
 │            │           │             │            │          │
 │            │ JSON result             │            │          │
 │            │<──────────│             │            │          │
 │            │           │             │            │          │
 │ Display    │           │             │            │          │
 │<───────────│           │             │            │          │
```

### Sequence 3: Multi-Agent Task (Sequential)

```
User      Browser   Flask   AutogenSvc  Agent1    Agent2    Agent3
 │           │        │          │         │         │         │
 │ Submit    │        │          │         │         │         │
 │  Task     │        │          │         │         │         │
 │──────────>│        │          │         │         │         │
 │           │        │          │         │         │         │
 │           │ POST /api/autogen/task/sequential    │         │
 │           │───────>│          │         │         │         │
 │           │        │          │         │         │         │
 │           │        │ sequential_task() │         │         │
 │           │        │─────────>│         │         │         │
 │           │        │          │         │         │         │
 │           │        │          │ initiate_chat()   │         │
 │           │        │          │────────>│         │         │
 │           │        │          │         │         │         │
 │           │        │          │ result1 │         │         │
 │           │        │          │<────────│         │         │
 │           │        │          │         │         │         │
 │           │        │          │ initiate_chat(result1)      │
 │           │        │          │─────────────────>│         │
 │           │        │          │         │         │         │
 │           │        │          │ result2 │         │         │
 │           │        │          │<─────────────────│         │
 │           │        │          │         │         │         │
 │           │        │          │ initiate_chat(result2)      │
 │           │        │          │─────────────────────────────>│
 │           │        │          │         │         │         │
 │           │        │          │ final result      │         │
 │           │        │          │<─────────────────────────────│
 │           │        │          │         │         │         │
 │           │        │ aggregate results   │         │         │
 │           │        │<─────────│         │         │         │
 │           │        │          │         │         │         │
 │           │ JSON response     │         │         │         │
 │           │<───────│          │         │         │         │
 │           │        │          │         │         │         │
 │ Display   │        │          │         │         │         │
 │<──────────│        │          │         │         │         │
```

---

## 🗄️ Database Schema

### ER Diagram

```
┌─────────────────┐
│      User       │
├─────────────────┤
│ id (PK)         │
│ username        │
│ email           │
│ created_at      │
└────────┬────────┘
         │ 1:N
         ▼
┌─────────────────────┐
│   ChatSession       │
├─────────────────────┤
│ id (PK)             │
│ user_id (FK)        │──────────┐
│ title               │          │
│ model_name          │          │
│ mode                │          │ 1:1
│ created_at          │          │
│ updated_at          │          ▼
│ archived            │   ┌──────────────────┐
│ pinned              │   │ SessionMetadata  │
└──────────┬──────────┘   ├──────────────────┤
           │ 1:N          │ id (PK)          │
           │              │ session_id (FK)  │
           ▼              │ temperature      │
┌──────────────────┐      │ max_tokens       │
│     Message      │      │ system_prompt    │
├──────────────────┤      │ total_messages   │
│ id (PK)          │      │ total_tokens     │
│ session_id (FK)  │      │ enabled_plugins  │
│ role             │      │ enabled_tools    │
│ content          │      │ enabled_agents   │
│ image_url        │      └──────────────────┘
│ tool_calls       │
│ tool_results     │      ┌──────────────────┐
│ agent_name       │      │ UserPreference   │
│ tokens_used      │      ├──────────────────┤
│ created_at       │      │ id (PK)          │
│ edited           │      │ user_id (FK)     │
│ parent_msg_id    │      │ theme            │
└──────────────────┘      │ sidebar_collapsed│
                          │ default_model    │
                          │ default_temp     │
                          │ stream_mode      │
                          │ autogen_enabled  │
                          │ mcp_enabled      │
                          └──────────────────┘
```

### Table Specifications

**Users**
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**ChatSessions**
```sql
CREATE TABLE chat_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    title VARCHAR(200) DEFAULT 'New Chat',
    model_name VARCHAR(100),
    mode VARCHAR(50) DEFAULT 'chat',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    archived BOOLEAN DEFAULT 0,
    pinned BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_sessions_user ON chat_sessions(user_id);
CREATE INDEX idx_sessions_updated ON chat_sessions(updated_at DESC);
```

**Messages**
```sql
CREATE TABLE messages (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    image_url VARCHAR(500),
    tool_calls JSON,
    tool_results JSON,
    agent_name VARCHAR(100),
    tokens_used INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    edited BOOLEAN DEFAULT 0,
    parent_message_id VARCHAR(36),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_message_id) REFERENCES messages(id)
);

CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_messages_created ON messages(created_at);
CREATE INDEX idx_messages_content ON messages(content);  -- For search
```

---

## 🔌 API Reference

### Session Management

**GET /api/sessions**
- Query params: `user_id`, `archived`
- Returns: List of sessions
- Example: `/api/sessions?user_id=default-user&archived=false`

**POST /api/sessions**
- Body: `{user_id, model_name, mode, title}`
- Returns: Created session
- Creates new chat session

**GET /api/sessions/{id}**
- Returns: Session details with messages
- Includes metadata and up to 50 recent messages

**PATCH /api/sessions/{id}**
- Body: `{title?, archived?, pinned?}`
- Returns: Success status
- Updates session properties

**DELETE /api/sessions/{id}**
- Returns: Success status
- Deletes session and all messages

**POST /api/sessions/{id}/messages**
- Body: `{role, content, image_url?, tool_calls?, agent_name?}`
- Returns: Created message
- Adds message to session

**GET /api/sessions/search**
- Query params: `user_id`, `q`
- Returns: Matching sessions
- Searches title and content

### MCP Tools

**POST /api/mcp/connect**
- Body: `{server_path}`
- Returns: Server info, tools, resources
- Connects to MCP server

**GET /api/mcp/status**
- Returns: Connection status
- Check if MCP server is connected

**GET /api/mcp/tools**
- Returns: List of available tools
- Tool name, description, parameters

**POST /api/mcp/tools/{name}/call**
- Body: `{arguments}`
- Returns: Tool execution result
- Executes specified tool

**GET /api/mcp/session/{id}/tools**
- Returns: Enabled tools for session
- Session-specific tool configuration

**PATCH /api/mcp/session/{id}/tools**
- Body: `{enabled_tools}`
- Returns: Success status
- Update enabled tools

### Autogen Agents

**GET /api/autogen/agents**
- Returns: List of available agents
- Agent name, description, capabilities

**POST /api/autogen/task/sequential**
- Body: `{task, agents, temperature?}`
- Returns: Conversation history and result
- Sequential agent workflow

**POST /api/autogen/task/group**
- Body: `{task, agents, max_round?, temperature?}`
- Returns: Conversation history and result
- Group chat workflow

**POST /api/autogen/image/enhance**
- Body: `{prompt}`
- Returns: Enhanced prompts workflow
- Image prompt enhancement

**GET /api/autogen/workflows**
- Returns: Available workflows
- Workflow templates and recommendations

### Plugins

**GET /api/plugins**
- Returns: List of plugins
- Plugin name, version, enabled status

**POST /api/plugins/discover**
- Returns: Discovered plugins
- Scans plugin directory

**POST /api/plugins/{name}/enable**
- Returns: Success status
- Enables plugin

**POST /api/plugins/{name}/disable**
- Returns: Success status
- Disables plugin

---

## 💻 Technology Stack

### Backend
- **Framework**: Flask 2.3.3
- **ORM**: SQLAlchemy 3.0.5
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Cache**: Redis 5.0.1 (optional)
- **AI Framework**: AutoGen 0.2.25 → 0.4.x (upgrading)
- **Protocol**: MCP 0.9.0
- **LLM Backend**: Ollama
- **Image Gen**: ComfyUI

### Frontend
- **HTML5/CSS3**: Modern responsive design
- **JavaScript**: ES6+ with async/await
- **Architecture**: Component-based managers
- **Communication**: REST API + Server-Sent Events (SSE)

### Development
- **Language**: Python 3.10+
- **Package Manager**: pip
- **Version Control**: Git
- **Environment**: python-dotenv

### External Services
- **Ollama**: Local LLM inference
- **ComfyUI**: Image generation workflows
- **MCP Tools**: External tool integrations

---

## 📊 Performance Considerations

### Optimization Strategies

1. **Database**
   - Indexes on frequently queried fields
   - Connection pooling
   - Lazy loading for relationships

2. **Caching**
   - Redis for active sessions
   - Browser localStorage for UI state
   - HTTP caching headers

3. **API**
   - Pagination for large lists
   - Streaming for real-time updates
   - Async operations for long tasks

4. **Frontend**
   - Code splitting
   - Lazy component loading
   - Debounced search inputs

### Scalability

**Horizontal Scaling**:
- Stateless API design
- Session storage in database
- Load balancer ready

**Vertical Scaling**:
- Async/await patterns
- Background task queues
- Database connection pooling

---

## 🔒 Security

### Authentication & Authorization
- User-based session isolation
- Input validation on all endpoints
- SQL injection prevention (ORM)

### Data Protection
- Secure session storage
- HTTPS recommended for production
- Environment-based secrets

### API Security
- CORS configuration
- Rate limiting (recommended)
- Input sanitization

---

## 📝 Deployment

### Development
```bash
python app_new.py
```

### Production Recommendations
```bash
# Use production WSGI server
gunicorn -w 4 -b 0.0.0.0:5000 app_new:app

# With PostgreSQL
export DATABASE_URI="postgresql://user:pass@localhost/ollama_webui"

# With Redis
export REDIS_ENABLED=true
export REDIS_HOST=localhost
```

---

**Last Updated**: 2025-01-26
**Version**: 2.0.0
**Status**: Complete Implementation
