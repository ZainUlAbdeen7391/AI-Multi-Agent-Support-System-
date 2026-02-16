import time
from datetime import datetime, UTC
from typing import List

AGENT_TIMEOUT_SECONDS = 1800


def monitor_tickets(tickets: List):
    """
    Periodically checks tickets for agent timeout or stuck state.
    """
    now = datetime.now(UTC)

    for ticket in tickets:
        if ticket.status == "processing":
            created_at = datetime.fromisoformat(ticket.created_at)
            elapsed = (now - created_at).total_seconds()

            if elapsed > AGENT_TIMEOUT_SECONDS:
                escalate_ticket(ticket, reason="Agent timeout")


def escalate_ticket(ticket, reason: str):
    ticket.status = "escalated"
    ticket.admin_required = True
    ticket.error = reason

    notify_admin(ticket)


def notify_admin(ticket):
    print(f"🚨 ADMIN ALERT: Ticket {ticket.id} escalated → {ticket.error}")






