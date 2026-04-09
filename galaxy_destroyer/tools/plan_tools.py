"""Plan mode tools for structured task planning"""

from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum

from galaxy_destroyer.tools.registry import register_tool, ToolCategory, ToolParameter


class PlanStatus(Enum):
    ACTIVE = "active"
    APPROVED = "approved"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class PlanStep:
    id: int
    description: str
    status: str = "pending"
    completed: bool = False


@dataclass
class Plan:
    id: str
    title: str
    description: str
    steps: list = field(default_factory=list)
    status: PlanStatus = PlanStatus.ACTIVE
    created_at: float = 0
    approved_at: Optional[float] = None


class PlanManager:
    def __init__(self):
        self._current_plan: Optional[Plan] = None

    def enter_plan_mode(self, title: str, description: str = "") -> Plan:
        self._current_plan = Plan(
            id=f"plan_{int(self._now())}",
            title=title,
            description=description,
            created_at=self._now(),
        )
        return self._current_plan

    def exit_plan_mode(self) -> Optional[Plan]:
        plan = self._current_plan
        self._current_plan = None
        return plan

    def get_current_plan(self) -> Optional[Plan]:
        return self._current_plan

    def add_step(self, description: str) -> PlanStep:
        if not self._current_plan:
            raise RuntimeError("Not in plan mode")

        step_id = len(self._current_plan.steps) + 1
        step = PlanStep(id=step_id, description=description)
        self._current_plan.steps.append(step)
        return step

    def update_step(self, step_id: int, completed: bool = None, status: str = None):
        if not self._current_plan:
            return

        for step in self._current_plan.steps:
            if step.id == step_id:
                if completed is not None:
                    step.completed = completed
                    step.status = "completed" if completed else "pending"
                if status is not None:
                    step.status = status
                break

    def approve_plan(self):
        if self._current_plan:
            self._current_plan.status = PlanStatus.APPROVED
            self._current_plan.approved_at = self._now()

    def complete_plan(self):
        if self._current_plan:
            self._current_plan.status = PlanStatus.COMPLETED

    def cancel_plan(self):
        if self._current_plan:
            self._current_plan.status = PlanStatus.CANCELLED

    def _now(self) -> float:
        import time

        return time.time()


_plan_manager: Optional[PlanManager] = None


def get_plan_manager() -> PlanManager:
    global _plan_manager
    if _plan_manager is None:
        _plan_manager = PlanManager()
    return _plan_manager


@register_tool(
    name="enter_plan_mode",
    description="Enter plan mode to outline steps before implementing",
    category=ToolCategory.PLAN,
    parameters=[
        ToolParameter(
            name="reason", description="Why you're entering plan mode", required=True
        ),
    ],
)
def enter_plan_mode(reason: str, _context: Any = None) -> Dict:
    manager = get_plan_manager()

    if manager.get_current_plan():
        return {
            "error": "Already in plan mode",
            "plan_id": manager.get_current_plan().id,
        }

    plan = manager.enter_plan_mode(title=reason, description=reason)

    return {
        "status": "plan_mode_entered",
        "plan_id": plan.id,
        "reason": reason,
        "message": "Plan mode active. Outline your steps, then use exit_plan_mode when ready.",
    }


@register_tool(
    name="exit_plan_mode",
    description="Exit plan mode and optionally approve the plan",
    category=ToolCategory.PLAN,
    parameters=[
        ToolParameter(
            name="approve",
            description="Approve the plan to proceed",
            type="boolean",
            default=False,
        ),
    ],
)
def exit_plan_mode(approve: bool = False, _context: Any = None) -> Dict:
    manager = get_plan_manager()
    plan = manager.get_current_plan()

    if not plan:
        return {"error": "Not in plan mode"}

    if approve:
        manager.approve_plan()
        return {
            "status": "plan_approved",
            "plan_id": plan.id,
            "plan": {
                "id": plan.id,
                "title": plan.title,
                "description": plan.description,
                "steps": [s.__dict__ for s in plan.steps],
                "status": plan.status.value,
            },
        }

    manager.exit_plan_mode()

    return {
        "status": "plan_mode_exited",
        "cancelled": True,
    }


@register_tool(
    name="add_plan_step",
    description="Add a step to the current plan",
    category=ToolCategory.PLAN,
    parameters=[
        ToolParameter(name="step", description="Step description", required=True),
    ],
)
def add_plan_step(step: str, _context: Any = None) -> Dict:
    manager = get_plan_manager()
    plan = manager.get_current_plan()

    if not plan:
        return {"error": "Not in plan mode. Use enter_plan_mode first."}

    plan_step = manager.add_step(step)

    return {
        "step_id": plan_step.id,
        "step": step,
        "total_steps": len(plan.steps),
    }


@register_tool(
    name="get_plan",
    description="Get the current plan",
    category=ToolCategory.PLAN,
)
def get_plan(_context: Any = None) -> Dict:
    manager = get_plan_manager()
    plan = manager.get_current_plan()

    if not plan:
        return {"status": "no_active_plan"}

    return {
        "id": plan.id,
        "title": plan.title,
        "description": plan.description,
        "status": plan.status.value,
        "steps": [
            {"id": s.id, "description": s.description, "status": s.status}
            for s in plan.steps
        ],
        "created_at": plan.created_at,
        "approved_at": plan.approved_at,
    }
