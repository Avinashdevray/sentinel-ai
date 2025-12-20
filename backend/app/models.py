from pydantic import BaseModel
from typing import Literal, Optional, Dict, Any, List
from enum import Enum


class RiskLevel(str, Enum):
    """Risk levels for actions"""
    HIGH = "HIGH"
    LOW = "LOW"


class ActionType(str, Enum):
    """Types of actions the agent can take"""
    CLICK = "click"
    TYPE = "type"
    WAIT = "wait"
    DONE = "done"
    NAVIGATE = "navigate"


class AgentAction(BaseModel):
    """Action to be performed by the agent"""
    action: ActionType
    selector: Optional[str] = None
    value: Optional[str] = None
    reasoning: str
    risk_level: RiskLevel
    confidence: float = 0.0


class AgentState(BaseModel):
    """State of the agent during execution"""
    messages: List[str] = []
    screenshot: Optional[str] = None
    next_action: Optional[AgentAction] = None
    status: Literal["RUNNING", "PAUSED", "DONE", "ERROR"] = "RUNNING"
    current_url: Optional[str] = None
    task: str = ""
    retry_count: int = 0
    max_retries: int = 3


class TaskRequest(BaseModel):
    """Request to execute a task"""
    task: str
    start_url: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Response from user for approval"""
    decision: Literal["APPROVE", "REJECT"]
    session_id: str


class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    type: Literal["TASK", "APPROVAL", "STATUS", "LOG", "ERROR", "APPROVAL_REQ", "COMPLETE"]
    data: Dict[str, Any]
    session_id: Optional[str] = None
