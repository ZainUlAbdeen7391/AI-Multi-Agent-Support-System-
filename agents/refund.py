from agents.base import BaseAgent

class RefundAgent(BaseAgent):
    SYSTEM = """
You handle refunds and cancellations.
Policies:
- 30-day return
- 5-7 business days refund
Be empathetic.
"""

    def __init__(self, client):
        super().__init__(client, "RefundAgent")
