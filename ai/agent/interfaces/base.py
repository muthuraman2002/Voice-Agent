from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class AgentAction(BaseModel):
    """Action to be taken by the agent"""
    type: str  # "respond", "tool_call", "search", etc.
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Response from the agent"""
    action: AgentAction
    conversation_state: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class Agent(ABC):
    """Abstract base class for AI agents"""

    @abstractmethod
    async def process(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Process user input and determine next action

        Args:
            user_input: User's text input
            conversation_history: Previous conversation messages
            context: Additional context (e.g., RAG results, user info)

        Returns:
            AgentResponse with action to take
        """
        pass

    @abstractmethod
    def get_conversation_state(self) -> Dict[str, Any]:
        """
        Get current conversation state

        Returns:
            Dictionary with conversation state
        """
        pass

    @abstractmethod
    def reset(self):
        """Reset agent state"""
        pass
