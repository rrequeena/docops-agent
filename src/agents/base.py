from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.agents.state import AgentState, AgentType


class BaseAgent(ABC):
    """Base class for all agents in the DocOps system."""

    def __init__(self, name: str, agent_type: AgentType):
        self.name = name
        self.agent_type = agent_type

    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        """Process the current state and return updated state."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    def validate_state(self, state: AgentState) -> bool:
        """Validate that the state has required fields for this agent."""
        return True

    def get_tools(self) -> list:
        """Return list of tools available to this agent."""
        return []


class AgentFactory:
    """Factory for creating agent instances."""

    _agents: Dict[str, BaseAgent] = {}

    @classmethod
    def register(cls, name: str, agent: BaseAgent):
        cls._agents[name] = agent

    @classmethod
    def get(cls, name: str) -> Optional[BaseAgent]:
        return cls._agents.get(name)

    @classmethod
    def list_agents(cls) -> list:
        return list(cls._agents.keys())


def create_agent_node(agent: BaseAgent):
    """Create a LangGraph node function from an agent instance."""

    def node(state: AgentState) -> AgentState:
        if not agent.validate_state(state):
            state["errors"].append(f"Invalid state for agent {agent.name}")
            return state

        try:
            updated_state = agent.process(state)
            updated_state["current_agent"] = agent.agent_type
            updated_state["step_count"] = state.get("step_count", 0) + 1
            return updated_state
        except Exception as e:
            state["errors"].append(f"Error in {agent.name}: {str(e)}")
            return state

    return node
