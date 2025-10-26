# AutoGen 0.7.5 Migration Guide

## Overview

This document outlines the migration from **pyautogen 0.2.25** to **autogen-agentchat 0.7.5**, which represents a major architectural shift in the Microsoft AutoGen framework.

## Key Changes

### Package Names
- **Old**: `pyautogen==0.2.25`
- **New**: `autogen-agentchat==0.7.5` + `autogen-ext[openai]==0.7.5`

### Architecture Changes

#### 1. **Async/Await Pattern**
All agent operations are now asynchronous:

**Before (0.2.25)**:
```python
from autogen import AssistantAgent, UserProxyAgent

agent = AssistantAgent(
    name="Assistant",
    llm_config={"config_list": config_list}
)

user_proxy.initiate_chat(agent, message="Hello")
```

**After (0.7.5)**:
```python
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

agent = AssistantAgent(
    name="Assistant",
    model_client=OpenAIChatCompletionClient(model="llama2")
)

# All operations are async
result = await agent.run(task="Hello")
```

#### 2. **Model Client Configuration**
- **Old**: `llm_config` dictionary with `config_list`
- **New**: Direct `model_client` instances

**Before**:
```python
config = {
    "config_list": [{
        "model": "llama2",
        "api_base": "http://localhost:11434/v1",
        "api_key": "ollama"
    }],
    "temperature": 0.7
}

agent = AssistantAgent(name="Agent", llm_config=config)
```

**After**:
```python
model_client = OpenAIChatCompletionClient(
    model="llama2",
    api_key="ollama",
    base_url="http://localhost:11434/v1"
)

agent = AssistantAgent(
    name="Agent",
    model_client=model_client
)
```

#### 3. **Team-Based Coordination**
- **Old**: `GroupChat` + `GroupChatManager`
- **New**: `RoundRobinGroupChat` or `SelectorGroupChat` teams

**Before**:
```python
from autogen import GroupChat, GroupChatManager

group_chat = GroupChat(
    agents=[agent1, agent2],
    messages=[],
    max_round=12
)

manager = GroupChatManager(
    groupchat=group_chat,
    llm_config=config
)

user_proxy.initiate_chat(manager, message="Task")
```

**After**:
```python
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination

termination = MaxMessageTermination(max_messages=12)

team = SelectorGroupChat(
    [agent1, agent2],
    model_client=model_client,
    termination_condition=termination
)

result = await team.run(task="Task")
```

#### 4. **Agent Descriptions**
Agents now have a `description` parameter (critical for SelectorGroupChat):

```python
agent = AssistantAgent(
    name="Researcher",
    description="Research assistant for gathering and analyzing information",
    model_client=model_client,
    system_message="You are a research assistant..."
)
```

#### 5. **Termination Conditions**
More explicit termination handling:

```python
from autogen_agentchat.conditions import (
    TextMentionTermination,
    MaxMessageTermination
)

# Combine conditions with | (OR)
termination = (
    MaxMessageTermination(max_messages=20) |
    TextMentionTermination("TERMINATE")
)
```

#### 6. **No More UserProxyAgent**
The `UserProxyAgent` is removed. Teams handle task execution directly:

**Before**:
```python
user_proxy = UserProxyAgent(
    name="User",
    human_input_mode="NEVER"
)
user_proxy.initiate_chat(agent, message="Task")
```

**After**:
```python
# Direct task execution
result = await agent.run(task="Task")

# Or with teams
result = await team.run(task="Task")
```

## Migration Checklist

### ✅ Completed Changes in Ollama WebUI

1. **Updated requirements.txt**:
   - ✅ Replaced `pyautogen==0.2.25`
   - ✅ Added `autogen-agentchat==0.7.5`
   - ✅ Added `autogen-ext[openai]==0.7.5`

2. **Rewrote autogen_service.py**:
   - ✅ All methods are now `async`
   - ✅ Uses `OpenAIChatCompletionClient` for model configuration
   - ✅ Implements `RoundRobinGroupChat` for sequential tasks
   - ✅ Implements `SelectorGroupChat` for group collaboration
   - ✅ Added agent descriptions for all agents
   - ✅ Removed `UserProxyAgent` dependency
   - ✅ Added `initialize_autogen_service()` async helper

3. **Updated routes/autogen.py**:
   - ✅ Added `run_async()` helper for Flask async compatibility
   - ✅ All task routes now use `run_async()` wrapper
   - ✅ Added `/initialize` endpoint for async initialization
   - ✅ Updated version info to "0.7.5"

## API Changes Summary

### Service Methods

| Method | Before (0.2.25) | After (0.7.5) |
|--------|----------------|---------------|
| `create_agents()` | Sync | `async def create_agents()` |
| `sequential_task()` | Sync | `async def sequential_task()` |
| `group_task()` | Sync | `async def group_task()` |
| `image_generation_workflow()` | Sync | `async def image_generation_workflow()` |

### Return Values

All async methods now return:
```python
{
    'task': str,
    'mode': str,
    'agents': List[str],
    'conversation': List[Dict],
    'final_result': str,
    'stop_reason': str  # New field
}
```

## Installation Instructions

### 1. Update Dependencies
```bash
pip install -r requirements.txt
```

### 2. Verify Python Version
AutoGen 0.7.5 requires **Python 3.10+**. Current system: **Python 3.13.7** ✅

### 3. Test Installation
```bash
python -c "from autogen_agentchat.agents import AssistantAgent; print('AutoGen 0.7.5 installed successfully')"
```

## Testing the Migration

### Test Agent Creation
```python
import asyncio
from services.autogen_service import initialize_autogen_service

async def test():
    service = await initialize_autogen_service()
    print(f"Created {len(service.agents)} agents")
    for agent in service.get_available_agents():
        print(f"  - {agent['name']}: {agent['description']}")

asyncio.run(test())
```

### Test Sequential Task
```bash
curl -X POST http://localhost:5000/api/autogen/test
```

### Test Group Chat
```bash
curl -X POST http://localhost:5000/api/autogen/task/group \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Discuss the benefits of Python for web development",
    "agents": ["researcher", "coder", "critic"],
    "max_round": 6
  }'
```

## Breaking Changes to Watch For

### 1. **Message Structure**
Messages now use typed classes instead of dictionaries:
```python
from autogen_agentchat.messages import TextMessage

# Messages have .source and .content attributes
for message in result.messages:
    print(f"{message.source}: {message.content}")
```

### 2. **Agent State Management**
Agents are stateful and should not be reused across unrelated conversations:
```python
# DON'T: Reuse the same agent instance
agent = AssistantAgent(...)
await agent.run(task="Task 1")  # State is retained
await agent.run(task="Task 2")  # Continues from previous state

# DO: Create new instances or clear state appropriately
```

### 3. **Tool Execution**
Tools are executed within the same `run()` call automatically:
```python
async def search_tool(query: str) -> str:
    """Search the web"""
    return f"Results for: {query}"

agent = AssistantAgent(
    name="Assistant",
    model_client=model_client,
    tools=[search_tool]  # Tools auto-execute during run()
)
```

## Performance Improvements

AutoGen 0.7.5 brings several performance benefits:

1. **Async I/O**: Non-blocking operations for better concurrency
2. **Efficient Message Passing**: Optimized team coordination
3. **Scalable Architecture**: Built on `autogen-core` for production systems
4. **Better Memory Management**: Stateful agents with explicit lifecycle

## Rollback Plan

If issues arise, rollback to 0.2.25:

```bash
pip uninstall autogen-agentchat autogen-ext autogen-core
pip install pyautogen==0.2.25
git checkout HEAD~1 -- services/autogen_service.py routes/autogen.py requirements.txt
```

## Additional Resources

- [AutoGen 0.7.5 Documentation](https://microsoft.github.io/autogen/stable/)
- [Migration Guide from 0.2](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/migration-guide.html)
- [AgentChat User Guide](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html)
- [API Reference](https://microsoft.github.io/autogen/stable/reference/python/autogen_agentchat.agents.html)

## Questions or Issues?

If you encounter any issues during migration:

1. Check the official [GitHub Releases](https://github.com/microsoft/autogen/releases) for known issues
2. Review the [Discussion Forum](https://github.com/microsoft/autogen/discussions)
3. Check our implementation in [services/autogen_service.py](services/autogen_service.py)

---

**Migration Date**: 2025-10-26
**Migrated By**: Claude Code Agent
**Status**: ✅ Complete - Ready for Testing
