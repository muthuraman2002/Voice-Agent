from typing import Optional, Dict, Any, List
from ai.agent.interfaces.base import Agent, AgentAction, AgentResponse
from ai.llm.interfaces.base import LLMProvider, Message


class SimpleAgent(Agent):
    """Simple LLM-based agent for Phase 1"""

    def __init__(
        self,
        llm_provider: LLMProvider,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize simple agent

        Args:
            llm_provider: LLM provider to use
            system_prompt: System prompt for the agent
        """
        self.llm_provider = llm_provider
        self.system_prompt = system_prompt or (
            "You are a helpful AI voice assistant. "
            "Provide clear, concise, and natural responses. "
            "Speak in a conversational tone as if you're having a real conversation."
        )
        self.conversation_state = {
            "messages": []
        }

    async def process(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process user input and generate response

        Args:
            user_input: User's text input
            conversation_history: Previous conversation messages
            context: Additional context

        Returns:
            AgentResponse
        """
        # Build message list
        messages = [
            Message(role="system", content=self.system_prompt)
        ]

        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                messages.append(
                    Message(role=msg["role"], content=msg["content"])
                )

        # Add current user input
        messages.append(Message(role="user", content=user_input))

        # Generate response
        response = await self.llm_provider.generate(
            messages=messages,
            temperature=0.7
        )

        # Update conversation state
        self.conversation_state["messages"].append({
            "role": "user",
            "content": user_input
        })
        self.conversation_state["messages"].append({
            "role": "assistant",
            "content": response.content
        })

        # Return agent response
        return AgentResponse(
            action=AgentAction(
                type="respond",
                content=response.content
            ),
            conversation_state=self.conversation_state.copy(),
            metadata={
                "llm_metadata": response.metadata
            }
        )

    def get_conversation_state(self) -> Dict[str, Any]:
        """Get current conversation state"""
        return self.conversation_state.copy()

    def reset(self):
        """Reset agent state"""
        self.conversation_state = {
            "messages": []
        }
