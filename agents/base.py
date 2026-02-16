import json
import re
from datetime import datetime, UTC


class BaseAgent:
    SYSTEM = ""

    def __init__(self, client, name):
        self.client = client
        self.name = name

    def respond(self, ticket):
        prompt = f"""
Customer Message:
{ticket.message}

Respond in JSON:
{{
  "response": "...",
  "confidence": 0.0-1.0,
  "reasoning": "..."
}}
"""
        try:
            text = self.client.generate(prompt, self.SYSTEM, timeout=1800)
            data = json.loads(re.search(r"\{.*\}", text, re.S).group())
            return data
        except Exception as e:
            raise RuntimeError(f"{self.name} failed: {e}")
