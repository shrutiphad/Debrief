import uuid
from datetime import datetime, date

from sqlalchemy import String, Text, Boolean, ForeignKey, Date, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class HCP(Base):
    """A Healthcare Professional the field rep engages with."""

    __tablename__ = "hcps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialty: Mapped[str] = mapped_column(String(255), nullable=True)
    institution: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(120), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    tier: Mapped[str] = mapped_column(String(20), default="B")  # A/B/C prescriber tier
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    interactions: Mapped[list["Interaction"]] = relationship(
        back_populates="hcp", cascade="all, delete-orphan", order_by="desc(Interaction.interaction_date)"
    )


class Interaction(Base):
    """A single logged touchpoint between a rep and an HCP."""

    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    hcp_id: Mapped[str] = mapped_column(ForeignKey("hcps.id"), nullable=False)

    rep_name: Mapped[str] = mapped_column(String(255), default="Field Rep")
    interaction_type: Mapped[str] = mapped_column(String(50), default="visit")  # visit/call/email/conference/sample_drop
    channel: Mapped[str] = mapped_column(String(20), default="structured")  # structured | chat
    interaction_date: Mapped[date] = mapped_column(Date, default=date.today)

    interaction_time: Mapped[str] = mapped_column(String(10), nullable=True)  # HH:MM, optional
    attendees: Mapped[list] = mapped_column(JSON, default=list)

    products_discussed: Mapped[list] = mapped_column(JSON, default=list)
    samples_dropped: Mapped[list] = mapped_column(JSON, default=list)
    materials_shared: Mapped[list] = mapped_column(JSON, default=list)

    topics_discussed: Mapped[str] = mapped_column(Text, nullable=True)
    outcomes: Mapped[str] = mapped_column(Text, nullable=True)   # key outcomes / agreements reached
    raw_notes: Mapped[str] = mapped_column(Text, nullable=True)  # original free-text / chat transcript
    summary: Mapped[str] = mapped_column(Text, nullable=True)    # LLM-generated summary
    sentiment: Mapped[str] = mapped_column(String(20), nullable=True)  # positive/neutral/negative — AI-inferred by
                                                                        # default, but reps can override manually

    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False)
    follow_up_notes: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    edit_history: Mapped[list] = mapped_column(JSON, default=list)  # audit trail of edits made via the agent

    hcp: Mapped["HCP"] = relationship(back_populates="interactions")
    follow_ups: Mapped[list["FollowUp"]] = relationship(back_populates="interaction", cascade="all, delete-orphan")


class FollowUp(Base):
    """A scheduled next action tied to an interaction."""

    __tablename__ = "follow_ups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    interaction_id: Mapped[str] = mapped_column(ForeignKey("interactions.id"), nullable=False)
    hcp_id: Mapped[str] = mapped_column(ForeignKey("hcps.id"), nullable=False)

    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/completed/cancelled

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    interaction: Mapped["Interaction"] = relationship(back_populates="follow_ups")
