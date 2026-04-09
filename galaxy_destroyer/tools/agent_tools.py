"""Agent tool for spawning sub-agents"""

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from galaxy_destroyer.tools.registry import register_tool, ToolCategory, ToolParameter


class AgentStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class Agent:
    id: str
    description: str
    prompt: str
    status: AgentStatus = AgentStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[str] = None
    error: Optional[str] = None
    subagent_type: str = "general-purpose"
    tools: List[str] = field(default_factory=list)


class AgentManager:
    def __init__(self):
        self._agents: Dict[str, Agent] = {}

    def create(
        self,
        description: str,
        prompt: str,
        subagent_type: str = "general-purpose",
        tools: Optional[List[str]] = None,
    ) -> Agent:
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        agent = Agent(
            id=agent_id,
            description=description,
            prompt=prompt,
            subagent_type=subagent_type,
            tools=tools or [],
        )
        self._agents[agent_id] = agent
        return agent

    def get(self, agent_id: str) -> Optional[Agent]:
        return self._agents.get(agent_id)

    def list(self) -> List[Agent]:
        return list(self._agents.values())

    def update_status(
        self,
        agent_id: str,
        status: AgentStatus,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ):
        agent = self._agents.get(agent_id)
        if agent:
            agent.status = status
            if status == AgentStatus.RUNNING:
                agent.started_at = time.time()
            if status in (
                AgentStatus.COMPLETED,
                AgentStatus.FAILED,
                AgentStatus.STOPPED,
            ):
                agent.completed_at = time.time()
            if result is not None:
                agent.result = result
            if error is not None:
                agent.error = error

    def stop(self, agent_id: str) -> bool:
        agent = self._agents.get(agent_id)
        if agent and agent.status == AgentStatus.RUNNING:
            agent.status = AgentStatus.STOPPED
            agent.completed_at = time.time()
            return True
        return False

    def cleanup_old(self, max_age_seconds: int = 3600):
        now = time.time()
        to_remove = [
            aid
            for aid, agent in self._agents.items()
            if agent.completed_at and now - agent.completed_at > max_age_seconds
        ]
        for aid in to_remove:
            del self._agents[aid]


_agent_manager: Optional[AgentManager] = None


def get_agent_manager() -> AgentManager:
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager


@register_tool(
    name="agent",
    description="Spawn a sub-agent to work on a task in parallel",
    category=ToolCategory.AGENT,
    parameters=[
        ToolParameter(
            name="prompt", description="Instructions for the agent", required=True
        ),
        ToolParameter(
            name="description",
            description="Brief description of the task",
            required=True,
        ),
        ToolParameter(
            name="subagent_type",
            description="Type of agent (general-purpose/explore/verification)",
            default="general-purpose",
        ),
    ],
)
def agent(
    prompt: str,
    description: str,
    subagent_type: str = "general-purpose",
    _context: Any = None,
) -> Dict:
    manager = get_agent_manager()

    agent_obj = manager.create(
        description=description,
        prompt=prompt,
        subagent_type=subagent_type,
    )

    asyncio.create_task(_run_agent(agent_obj.id, prompt, subagent_type))

    return {
        "agent_id": agent_obj.id,
        "description": description,
        "status": agent_obj.status.value,
        "message": f"Spawned agent: {description}",
    }


async def _run_agent(agent_id: str, prompt: str, subagent_type: str):
    manager = get_agent_manager()
    manager.update_status(agent_id, AgentStatus.RUNNING)

    try:
        from services.api import create_client
        from services.agents import get_agent_prompt

        system_prompt = get_agent_prompt(subagent_type)
        full_prompt = f"{system_prompt}\n\nTask:\n{prompt}"

        client = create_client()

        response = await asyncio.wait_for(
            client.send_message(
                system_prompt=full_prompt,
                message=prompt,
            ),
            timeout=300,
        )

        manager.update_status(
            agent_id,
            AgentStatus.COMPLETED,
            result=response.message.content
            if hasattr(response, "message")
            else str(response),
        )
    except asyncio.TimeoutError:
        manager.update_status(agent_id, AgentStatus.FAILED, error="Agent timed out")
    except Exception as e:
        manager.update_status(agent_id, AgentStatus.FAILED, error=str(e))


@register_tool(
    name="send_message",
    description="Send a message to a running agent",
    category=ToolCategory.AGENT,
    parameters=[
        ToolParameter(name="agent_id", description="Agent ID", required=True),
        ToolParameter(name="message", description="Message to send", required=True),
    ],
)
def send_message(agent_id: str, message: str, _context: Any = None) -> Dict:
    manager = get_agent_manager()
    agent = manager.get(agent_id)

    if not agent:
        return {"error": f"Agent not found: {agent_id}"}

    if agent.status not in (AgentStatus.RUNNING, AgentStatus.COMPLETED):
        return {
            "error": f"Agent is not in a state to receive messages: {agent.status.value}"
        }

    return {
        "agent_id": agent_id,
        "status": "message_queued",
        "message": "Message sent to agent",
    }


@register_tool(
    name="task_status",
    description="Check status of an agent",
    category=ToolCategory.AGENT,
    parameters=[
        ToolParameter(name="agent_id", description="Agent ID", required=True),
    ],
)
def task_status(agent_id: str, _context: Any = None) -> Dict:
    manager = get_agent_manager()
    agent = manager.get(agent_id)

    if not agent:
        return {"error": f"Agent not found: {agent_id}"}

    result = {
        "agent_id": agent.id,
        "description": agent.description,
        "status": agent.status.value,
        "created_at": agent.created_at,
    }

    if agent.started_at:
        result["started_at"] = agent.started_at
    if agent.completed_at:
        result["completed_at"] = agent.completed_at
    if agent.result:
        result["result"] = agent.result
    if agent.error:
        result["error"] = agent.error

    return result


@register_tool(
    name="task_output",
    description="Get output from completed agent",
    category=ToolCategory.AGENT,
    parameters=[
        ToolParameter(name="agent_id", description="Agent ID", required=True),
    ],
)
def task_output(agent_id: str, _context: Any = None) -> Dict:
    manager = get_agent_manager()
    agent = manager.get(agent_id)

    if not agent:
        return {"error": f"Agent not found: {agent_id}"}

    if agent.status != AgentStatus.COMPLETED:
        return {
            "agent_id": agent_id,
            "status": agent.status.value,
            "result": agent.result,
            "error": agent.error,
        }

    return {
        "agent_id": agent_id,
        "status": agent.status.value,
        "result": agent.result,
    }
