"""
Autogen Service - Multi-agent system using Microsoft AutoGen
"""
from typing import List, Dict, Any, Optional
import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
import json

class AutogenService:
    """Multi-agent system using AutoGen"""

    def __init__(self, ollama_base_url="http://localhost:11434"):
        self.ollama_base_url = ollama_base_url
        self.config_list = [{
            "model": "llama2",
            "api_base": f"{ollama_base_url}/v1",
            "api_key": "ollama",  # Ollama doesn't need a real API key
            "api_type": "open_ai"
        }]
        self.agents = {}
        self.group_chat = None
        self.manager = None
        self.conversation_history = []

    def create_agents(self, temperature: float = 0.7):
        """Create specialized agents

        Args:
            temperature: Temperature for LLM responses
        """
        base_config = {
            "config_list": self.config_list,
            "temperature": temperature,
        }

        # Researcher Agent
        self.agents['researcher'] = AssistantAgent(
            name="Researcher",
            llm_config=base_config,
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
            llm_config={**base_config, "temperature": 0.3},  # Lower temp for coding
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
            llm_config={**base_config, "temperature": 0.9},  # Higher temp for creativity
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
            llm_config=base_config,
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
            llm_config={**base_config, "temperature": 0.5},
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
            llm_config=base_config,
            system_message="""You are a strategic planner. Your role is to:
- Break down complex tasks into steps
- Create actionable plans
- Coordinate between different agents
- Prioritize tasks effectively
- Ensure goals are met

Be organized, systematic, and goal-oriented."""
        )

        # User Proxy (represents the human user)
        self.agents['user_proxy'] = UserProxyAgent(
            name="User",
            human_input_mode="NEVER",  # Fully automated
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config=False,  # Disable code execution for safety
        )

        print(f"✓ Created {len(self.agents)} agents")

    def setup_group_chat(self, agent_names: List[str], max_round: int = 12):
        """Setup group chat with specified agents

        Args:
            agent_names: List of agent names to include
            max_round: Maximum number of conversation rounds
        """
        agent_list = []

        for name in agent_names:
            if name in self.agents:
                agent_list.append(self.agents[name])
            else:
                print(f"Warning: Agent '{name}' not found")

        if not agent_list:
            raise ValueError("No valid agents specified")

        self.group_chat = GroupChat(
            agents=agent_list,
            messages=[],
            max_round=max_round,
            speaker_selection_method="auto",  # or "round_robin", "manual"
        )

        self.manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config={"config_list": self.config_list}
        )

        print(f"✓ Group chat setup with {len(agent_list)} agents")

    def sequential_task(self, task: str, agent_names: List[str]) -> Dict[str, Any]:
        """Execute task sequentially across agents

        Args:
            task: The task description
            agent_names: Ordered list of agent names

        Returns:
            Task results with conversation history
        """
        if 'user_proxy' not in self.agents:
            self.create_agents()

        current_result = task
        conversation = []

        for agent_name in agent_names:
            if agent_name not in self.agents or agent_name == 'user_proxy':
                continue

            agent = self.agents[agent_name]
            user_proxy = self.agents['user_proxy']

            # Start conversation
            try:
                user_proxy.initiate_chat(
                    agent,
                    message=current_result,
                    max_turns=1
                )

                # Get last message as result
                if hasattr(agent, 'last_message') and callable(agent.last_message):
                    last_msg = agent.last_message()
                    current_result = last_msg.get("content", current_result) if isinstance(last_msg, dict) else str(last_msg)

                conversation.append({
                    'agent': agent_name,
                    'message': current_result
                })

            except Exception as e:
                print(f"Error with agent {agent_name}: {e}")
                conversation.append({
                    'agent': agent_name,
                    'error': str(e)
                })

        return {
            'task': task,
            'mode': 'sequential',
            'agents': agent_names,
            'conversation': conversation,
            'final_result': current_result
        }

    def group_task(self, task: str, agent_names: List[str], max_round: int = 12) -> Dict[str, Any]:
        """Execute task as group collaboration

        Args:
            task: The task description
            agent_names: List of agent names to collaborate
            max_round: Maximum conversation rounds

        Returns:
            Task results with full conversation
        """
        if not self.agents:
            self.create_agents()

        # Ensure user_proxy is included
        if 'user_proxy' not in agent_names:
            agent_names = ['user_proxy'] + agent_names

        try:
            self.setup_group_chat(agent_names, max_round)

            user_proxy = self.agents['user_proxy']
            user_proxy.initiate_chat(self.manager, message=task)

            # Extract conversation
            conversation = []
            if self.group_chat:
                for msg in self.group_chat.messages:
                    conversation.append({
                        'agent': msg.get('name', 'unknown'),
                        'content': msg.get('content', ''),
                        'role': msg.get('role', 'assistant')
                    })

            final_result = conversation[-1]['content'] if conversation else "No result"

            return {
                'task': task,
                'mode': 'group',
                'agents': agent_names,
                'conversation': conversation,
                'final_result': final_result,
                'total_rounds': len(conversation)
            }

        except Exception as e:
            return {
                'task': task,
                'mode': 'group',
                'agents': agent_names,
                'error': str(e),
                'conversation': []
            }

    def image_generation_workflow(self, user_prompt: str) -> Dict[str, Any]:
        """Specialized workflow for image generation

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
            self.create_agents()

        workflow_steps = []

        # Step 1: Creative enhancement
        creative = self.agents.get('creative')
        user_proxy = self.agents['user_proxy']

        if not creative or not user_proxy:
            return {'error': 'Required agents not available'}

        try:
            # Creative enhancement
            user_proxy.initiate_chat(
                creative,
                message=f"Enhance this image prompt creatively, adding artistic details: {user_prompt}",
                max_turns=1
            )

            enhanced_msg = creative.last_message() if hasattr(creative, 'last_message') else {}
            enhanced_prompt = enhanced_msg.get("content", user_prompt) if isinstance(enhanced_msg, dict) else str(enhanced_msg)

            workflow_steps.append({
                'step': 'creative_enhancement',
                'agent': 'creative',
                'result': enhanced_prompt
            })

            # Step 2: Critic review
            critic = self.agents.get('critic')
            if critic:
                user_proxy.initiate_chat(
                    critic,
                    message=f"Review this enhanced image prompt and suggest improvements:\n{enhanced_prompt}",
                    max_turns=1
                )

                reviewed_msg = critic.last_message() if hasattr(critic, 'last_message') else {}
                reviewed_prompt = reviewed_msg.get("content", enhanced_prompt) if isinstance(reviewed_msg, dict) else str(reviewed_msg)

                workflow_steps.append({
                    'step': 'critic_review',
                    'agent': 'critic',
                    'result': reviewed_prompt
                })
            else:
                reviewed_prompt = enhanced_prompt

            # Step 3: Image specialist final prompt
            image_specialist = self.agents.get('image_specialist')
            if image_specialist:
                user_proxy.initiate_chat(
                    image_specialist,
                    message=f"""Based on this reviewed prompt, create a final technical prompt for image generation.
Include:
- Detailed visual description
- Art style and technique
- Lighting and composition
- Color palette
- Technical details (resolution, quality)
- Appropriate negative prompt

Reviewed prompt: {reviewed_prompt}""",
                    max_turns=1
                )

                final_msg = image_specialist.last_message() if hasattr(image_specialist, 'last_message') else {}
                final_output = final_msg.get("content", reviewed_prompt) if isinstance(final_msg, dict) else str(final_msg)

                workflow_steps.append({
                    'step': 'technical_prompt',
                    'agent': 'image_specialist',
                    'result': final_output
                })
            else:
                final_output = reviewed_prompt

            return {
                'original': user_prompt,
                'workflow': workflow_steps,
                'final_prompt': final_output,
                'success': True
            }

        except Exception as e:
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
            if name == 'user_proxy':
                continue

            info = {
                'name': name,
                'system_message': agent.system_message if hasattr(agent, 'system_message') else '',
                'type': 'assistant'
            }
            agent_info.append(info)

        return agent_info

    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        if self.group_chat:
            self.group_chat.messages = []

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
        _autogen_service.create_agents()
    return _autogen_service
