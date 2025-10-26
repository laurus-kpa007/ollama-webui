"""
Autogen Service - Multi-agent system using Microsoft AutoGen 0.7.5
Updated to use autogen-agentchat async API
"""
from typing import List, Dict, Any, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import asyncio
import json


class AutogenService:
    """Multi-agent system using AutoGen 0.7.5"""

    def __init__(self, ollama_base_url="http://localhost:11434"):
        self.ollama_base_url = ollama_base_url

        # Create model client for Ollama (OpenAI-compatible API)
        self.model_client = OpenAIChatCompletionClient(
            model="llama2",
            api_key="ollama",  # Ollama doesn't need a real API key
            base_url=f"{ollama_base_url}/v1"
        )

        self.agents = {}
        self.conversation_history = []

    async def create_agents(self, temperature: float = 0.7):
        """Create specialized agents (async)

        Args:
            temperature: Temperature for LLM responses
        """
        # Researcher Agent
        self.agents['researcher'] = AssistantAgent(
            name="Researcher",
            description="Research assistant for gathering and analyzing information",
            model_client=self.model_client,
            system_message="""You are a research assistant. Your role is to:
- Gather and analyze information
- Provide comprehensive research summaries
- Find relevant data and insights
- Cite sources when available
- Ask clarifying questions when needed

Be thorough, accurate, and analytical in your research."""
        )

        # Coder Agent
        self.agents['coder'] = AssistantAgent(
            name="Coder",
            description="Senior software engineer for coding tasks",
            model_client=self.model_client,
            system_message="""You are a senior software engineer. Your role is to:
- Write clean, efficient, and maintainable code
- Debug and fix issues
- Suggest architectural improvements
- Follow best practices and coding standards
- Write comprehensive documentation

Provide code examples and explanations."""
        )

        # Creative Agent
        self.agents['creative'] = AssistantAgent(
            name="Creative",
            description="Creative specialist for innovative ideas and content",
            model_client=self.model_client,
            system_message="""You are a creative specialist. Your role is to:
- Generate innovative ideas and solutions
- Write engaging narratives and content
- Think outside the box
- Provide unique perspectives
- Design creative solutions

Be imaginative, original, and inspiring."""
        )

        # Image Specialist Agent
        self.agents['image_specialist'] = AssistantAgent(
            name="ImageSpecialist",
            description="Image generation expert for creating detailed prompts",
            model_client=self.model_client,
            system_message="""You are an image generation expert. Your role is to:
- Create detailed image generation prompts
- Enhance user prompts with artistic details
- Understand different art styles and techniques
- Provide appropriate negative prompts
- Suggest optimal generation parameters

Focus on visual quality, composition, and artistic elements."""
        )

        # Critic/Reviewer Agent
        self.agents['critic'] = AssistantAgent(
            name="Critic",
            description="Quality reviewer for critical analysis and feedback",
            model_client=self.model_client,
            system_message="""You are a quality reviewer. Your role is to:
- Review outputs from other agents critically
- Provide constructive feedback
- Ensure quality and accuracy
- Suggest improvements
- Identify potential issues

Be objective, thorough, and helpful in your reviews."""
        )

        # Planner Agent
        self.agents['planner'] = AssistantAgent(
            name="Planner",
            description="Strategic planner for task coordination and planning",
            model_client=self.model_client,
            system_message="""You are a strategic planner. Your role is to:
- Break down complex tasks into steps
- Create actionable plans
- Coordinate between different agents
- Prioritize tasks effectively
- Ensure goals are met

Be organized, systematic, and goal-oriented."""
        )

        print(f"✓ Created {len(self.agents)} agents")

    async def sequential_task(self, task: str, agent_names: List[str]) -> Dict[str, Any]:
        """Execute task sequentially across agents (async)

        Args:
            task: The task description
            agent_names: Ordered list of agent names

        Returns:
            Task results with conversation history
        """
        if not self.agents:
            await self.create_agents()

        conversation = []
        current_message = task

        # Create RoundRobinGroupChat for sequential execution
        agent_list = []
        for agent_name in agent_names:
            if agent_name in self.agents:
                agent_list.append(self.agents[agent_name])
            else:
                print(f"Warning: Agent '{agent_name}' not found")

        if not agent_list:
            return {
                'task': task,
                'mode': 'sequential',
                'agents': agent_names,
                'error': 'No valid agents specified',
                'conversation': []
            }

        try:
            # Create termination condition
            termination = MaxMessageTermination(max_messages=len(agent_list) * 2) | TextMentionTermination("TERMINATE")

            # Create round-robin team
            team = RoundRobinGroupChat(agent_list, termination_condition=termination)

            # Run the task
            result = await team.run(task=task)

            # Extract conversation from result
            for message in result.messages:
                conversation.append({
                    'agent': message.source if hasattr(message, 'source') else 'unknown',
                    'content': message.content if hasattr(message, 'content') else str(message),
                    'type': type(message).__name__
                })

            final_result = conversation[-1]['content'] if conversation else "No result"

            return {
                'task': task,
                'mode': 'sequential',
                'agents': agent_names,
                'conversation': conversation,
                'final_result': final_result,
                'stop_reason': result.stop_reason if hasattr(result, 'stop_reason') else 'completed'
            }

        except Exception as e:
            print(f"Error in sequential task: {e}")
            return {
                'task': task,
                'mode': 'sequential',
                'agents': agent_names,
                'error': str(e),
                'conversation': conversation
            }

    async def group_task(self, task: str, agent_names: List[str], max_round: int = 12) -> Dict[str, Any]:
        """Execute task as group collaboration (async)

        Args:
            task: The task description
            agent_names: List of agent names to collaborate
            max_round: Maximum conversation rounds

        Returns:
            Task results with full conversation
        """
        if not self.agents:
            await self.create_agents()

        agent_list = []
        for agent_name in agent_names:
            if agent_name in self.agents:
                agent_list.append(self.agents[agent_name])
            else:
                print(f"Warning: Agent '{agent_name}' not found")

        if not agent_list:
            return {
                'task': task,
                'mode': 'group',
                'agents': agent_names,
                'error': 'No valid agents specified',
                'conversation': []
            }

        try:
            # Create termination condition
            termination = MaxMessageTermination(max_messages=max_round) | TextMentionTermination("TERMINATE")

            # Create selector-based group chat (dynamic speaker selection)
            team = SelectorGroupChat(
                agent_list,
                model_client=self.model_client,
                termination_condition=termination
            )

            # Run the task
            result = await team.run(task=task)

            # Extract conversation
            conversation = []
            for message in result.messages:
                conversation.append({
                    'agent': message.source if hasattr(message, 'source') else 'unknown',
                    'content': message.content if hasattr(message, 'content') else str(message),
                    'type': type(message).__name__
                })

            final_result = conversation[-1]['content'] if conversation else "No result"

            return {
                'task': task,
                'mode': 'group',
                'agents': agent_names,
                'conversation': conversation,
                'final_result': final_result,
                'total_rounds': len(conversation),
                'stop_reason': result.stop_reason if hasattr(result, 'stop_reason') else 'completed'
            }

        except Exception as e:
            print(f"Error in group task: {e}")
            return {
                'task': task,
                'mode': 'group',
                'agents': agent_names,
                'error': str(e),
                'conversation': []
            }

    async def image_generation_workflow(self, user_prompt: str) -> Dict[str, Any]:
        """Specialized workflow for image generation (async)

        Workflow:
        1. Creative agent enhances the prompt
        2. Critic reviews the enhanced prompt
        3. Image specialist creates final technical prompt

        Args:
            user_prompt: User's original image prompt

        Returns:
            Enhanced prompts and workflow results
        """
        if not self.agents:
            await self.create_agents()

        workflow_steps = []

        # Get required agents
        creative = self.agents.get('creative')
        critic = self.agents.get('critic')
        image_specialist = self.agents.get('image_specialist')

        if not all([creative, critic, image_specialist]):
            return {'error': 'Required agents not available'}

        try:
            # Step 1: Creative enhancement
            creative_task = f"Enhance this image prompt creatively, adding artistic details: {user_prompt}"
            creative_result = await creative.run(task=creative_task)

            enhanced_prompt = creative_result.messages[-1].content if creative_result.messages else user_prompt

            workflow_steps.append({
                'step': 'creative_enhancement',
                'agent': 'creative',
                'result': enhanced_prompt
            })

            # Step 2: Critic review
            critic_task = f"Review this enhanced image prompt and suggest improvements:\n{enhanced_prompt}"
            critic_result = await critic.run(task=critic_task)

            reviewed_prompt = critic_result.messages[-1].content if critic_result.messages else enhanced_prompt

            workflow_steps.append({
                'step': 'critic_review',
                'agent': 'critic',
                'result': reviewed_prompt
            })

            # Step 3: Image specialist final prompt
            specialist_task = f"""Based on this reviewed prompt, create a final technical prompt for image generation.
Include:
- Detailed visual description
- Art style and technique
- Lighting and composition
- Color palette
- Technical details (resolution, quality)
- Appropriate negative prompt

Reviewed prompt: {reviewed_prompt}"""

            specialist_result = await image_specialist.run(task=specialist_task)
            final_output = specialist_result.messages[-1].content if specialist_result.messages else reviewed_prompt

            workflow_steps.append({
                'step': 'technical_prompt',
                'agent': 'image_specialist',
                'result': final_output
            })

            return {
                'original': user_prompt,
                'workflow': workflow_steps,
                'final_prompt': final_output,
                'success': True
            }

        except Exception as e:
            print(f"Error in image generation workflow: {e}")
            return {
                'original': user_prompt,
                'error': str(e),
                'workflow': workflow_steps,
                'success': False
            }

    def get_available_agents(self) -> List[Dict[str, str]]:
        """Get list of available agents with descriptions

        Returns:
            List of agent information
        """
        agent_info = []

        for name, agent in self.agents.items():
            info = {
                'name': name,
                'display_name': agent.name if hasattr(agent, 'name') else name,
                'description': agent.description if hasattr(agent, 'description') else '',
                'system_message': agent._system_messages[0].content if hasattr(agent, '_system_messages') and agent._system_messages else '',
                'type': 'assistant'
            }
            agent_info.append(info)

        return agent_info

    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []


# Singleton instance
_autogen_service = None


def get_autogen_service() -> AutogenService:
    """Get the global AutoGen service instance

    Returns:
        AutogenService instance
    """
    global _autogen_service
    if _autogen_service is None:
        _autogen_service = AutogenService()
        # Note: create_agents() is now async, so it should be called when needed
    return _autogen_service


async def initialize_autogen_service() -> AutogenService:
    """Initialize the AutoGen service asynchronously

    Returns:
        AutogenService instance with agents created
    """
    service = get_autogen_service()
    if not service.agents:
        await service.create_agents()
    return service
