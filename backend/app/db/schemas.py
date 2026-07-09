from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------- HCP ----------

class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    institution: Optional[str] = None
    city: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    tier: str = "B"


class HCPCreate(HCPBase):
    pass


class HCPOut(HCPBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


# ---------- Interaction ----------

class InteractionBase(BaseModel):
    hcp_id: str
    rep_name: str = "Field Rep"
    interaction_type: str = "visit"
    channel: str = "structured"
    interaction_date: date = date.today()
    interaction_time: Optional[str] = None
    attendees: list[str] = []
    products_discussed: list[str] = []
    samples_dropped: list[str] = []
    materials_shared: list[str] = []
    topics_discussed: Optional[str] = None
    outcomes: Optional[str] = None
    sentiment: Optional[str] = None  # manual override; if omitted, the LLM infers it
    raw_notes: Optional[str] = None
    follow_up_required: bool = False
    follow_up_notes: Optional[str] = None


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    """All fields optional — used for both the manual edit form and the
    LangGraph `edit_interaction` tool, which only patches what changed."""
    interaction_type: Optional[str] = None
    interaction_date: Optional[date] = None
    interaction_time: Optional[str] = None
    attendees: Optional[list[str]] = None
    products_discussed: Optional[list[str]] = None
    samples_dropped: Optional[list[str]] = None
    materials_shared: Optional[list[str]] = None
    topics_discussed: Optional[str] = None
    outcomes: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_notes: Optional[str] = None


class InteractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    hcp_id: str
    rep_name: str
    interaction_type: str
    channel: str
    interaction_date: date
    interaction_time: Optional[str]
    attendees: list[str]
    products_discussed: list[str]
    samples_dropped: list[str]
    materials_shared: list[str]
    topics_discussed: Optional[str]
    outcomes: Optional[str]
    raw_notes: Optional[str]
    summary: Optional[str]
    sentiment: Optional[str]
    follow_up_required: bool
    follow_up_notes: Optional[str]
    edit_history: list
    created_at: datetime
    updated_at: datetime


# ---------- FollowUp ----------

class FollowUpOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    interaction_id: str
    hcp_id: str
    due_date: date
    notes: Optional[str]
    status: str
    created_at: datetime


# ---------- Chat / Agent ----------

class ChatMessageIn(BaseModel):
    session_id: str
    hcp_id: Optional[str] = None
    message: str


class ToolTrace(BaseModel):
    tool: str
    input: dict
    output: dict
    status: str  # success | error


class ChatMessageOut(BaseModel):
    session_id: str
    reply: str
    tool_trace: list[ToolTrace]
    model_used: str
