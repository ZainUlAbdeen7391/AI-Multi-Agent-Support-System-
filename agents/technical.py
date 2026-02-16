from agents.base import BaseAgent

class TechnicalAgent(BaseAgent):
    SYSTEM = """
You troubleshoot technical issues.
Provide steps.
Ask clarifying questions if needed.
"""

    def __init__(self, client):
        super().__init__(client, "TechnicalAgent")
