from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime, UTC
import uuid


class Intent(str, Enum):
    REFUND = "refund"
    TECHNICAL = "technical"
    GENERAL = "general"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Ticket:
    id: str
    guest_email: str
    message: str
    intent: Optional[Intent] = None
    confidence: float = 0.0
    status: str = "new"
    assigned_agent: Optional[str] = None
    created_at: str = datetime.now(UTC).isoformat()
    response: Optional[str] = None
    admin_required: bool = False
    error: Optional[str] = None

    @staticmethod
    def create(message: str, email: str):
        return Ticket(
            id=str(uuid.uuid4()),
            guest_email=email,
            message=message
        )
