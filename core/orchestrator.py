import json
import re
from models import Intent, ConfidenceLevel


class OrchestratorAI:
    SYSTEM = """
You classify customer tickets.
Return STRICT JSON:

{
  "intent": "refund|technical|general",
  "confidence": 0.0-1.0,
  "reasoning": "short"
}
"""

    def __init__(self, client):
        self.client = client

    def classify(self, message: str):
        response = self.client.generate(message, self.SYSTEM)
        data = json.loads(re.search(r"\{.*\}", response, re.S).group())

        confidence = float(data["confidence"])

        if confidence >= 0.8:
            level = ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            level = ConfidenceLevel.MEDIUM
        else:
            level = ConfidenceLevel.LOW

        return Intent(data["intent"]), confidence, level
