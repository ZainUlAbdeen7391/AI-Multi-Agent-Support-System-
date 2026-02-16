from agents.base import BaseAgent

class GeneralAgent(BaseAgent):
    SYSTEM = """
General inquiries.
Hours: Mon-Fri 9–6 EST
Email: support@company.com
"""

    def __init__(self, client):
        super().__init__(client, "GeneralAgent")
