from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Dict, Optional, List
from enum import Enum
from datetime import datetime, UTC
import uuid
import threading
import time
import requests
import json
import re

def extract_json_safe(text: str) -> dict:
    try:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise ValueError("No JSON found in AI response")

        return json.loads(match.group())

    except Exception as e:
        print("❌ AI RAW RESPONSE:\n", text)
        raise RuntimeError("AI returned invalid JSON")


# =========================================================
# CONFIG
# =========================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama2"
AGENT_TIMEOUT = 1800  # seconds

# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(title="AI Support Ticket System (Single File)")

# In-memory DB
TICKETS: Dict[str, dict] = {}

# =========================================================
# ENUMS
# =========================================================

class Intent(str, Enum):
    refund = "refund"
    technical = "technical"
    general = "general"


class ConfidenceLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

# =========================================================
# OLLAMA CLIENT
# =========================================================

def ollama_generate(prompt: str, system: str, temperature=0.1, timeout=1800) -> str:
    try:
        payload = {
            "model": MODEL,
            "prompt": prompt,
            "system": system,
            "temperature": temperature,
            "stream": False
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        response.raise_for_status()

        data = response.json()

        if "response" not in data:
            raise ValueError("Missing 'response' field")

        return data["response"]

    except Exception as e:
        print("❌ Ollama failure:", str(e))
        raise RuntimeError("LLM service unavailable")

# =========================================================
# ORCHESTRATOR AI
# =========================================================

ORCHESTRATOR_SYSTEM = """
You classify customer support tickets.

Return STRICT JSON:
{
  "intent": "refund|technical|general",
  "confidence": 0.0-1.0,
  "reasoning": "short"
}
"""

def classify_ticket(message: str):
    try:
        text = ollama_generate(message, ORCHESTRATOR_SYSTEM)
        data = extract_json_safe(text)

        confidence = float(data.get("confidence", 0.0))
        intent = data.get("intent", "general")

        if confidence >= 0.8:
            level = ConfidenceLevel.high
        elif confidence >= 0.5:
            level = ConfidenceLevel.medium
        else:
            level = ConfidenceLevel.low

        return intent, confidence, level, data.get("reasoning", "")

    except Exception as e:
        print("❌ Classification failed:", str(e))
        return "general", 0.0, ConfidenceLevel.low, "Fallback due to error"


# =========================================================
# 
# =========================================================

import json

def agent_response(system_prompt: str, message: str):
    try:
       
        safe_message = json.dumps(message)  

        prompt = f"""
Customer Message:
{safe_message}

Return STRICT JSON ONLY:
{{
  "response": "...",
  "confidence": 0.0-1.0,
  "reasoning": "..."
}}
"""

        text = ollama_generate(prompt, system_prompt, temperature=0.0)

        # extract JSON safely
        return extract_json_safe(text)

    except Exception as e:
        print(f"❌ Agent failed for message: {message}")
        print("Error:", str(e))

        # fallback response
        return {
            "response": "Thank you for your message. Our support team will review it and get back to you shortly.",
            "confidence": 0.0,
            "reasoning": f"Fallback due to agent error: {str(e)}",
            "error": str(e)
        }


# =========================================================
# CONFIDENCE ROUTER
# =========================================================

def routing_action(confidence: float):
    if confidence >= 0.8:
        return "auto_respond"
    elif confidence >= 0.5:
        return "pending_admin"
    return "admin_only"

# =========================================================
# DUPLICATE CHECK
# =========================================================

def is_duplicate(email: str, message: str):
    for t in TICKETS.values():
        if t["guest_email"] == email and t["status"] != "closed":
            if message.lower() in t["message"].lower():
                return True, t["id"]
    return False, None

# =========================================================
# BACKGROUND ESCALATION
# =========================================================

def background_monitor():
    while True:
        now = datetime.now(UTC)
        for t in TICKETS.values():
            if t["status"] == "processing":
                created = datetime.fromisoformat(t["created_at"])
                if (now - created).total_seconds() > AGENT_TIMEOUT:
                    t["status"] = "escalated"
                    t["admin_required"] = True
                    t["error"] = "Agent timeout"
        time.sleep(5)

threading.Thread(target=background_monitor, daemon=True).start()

# =========================================================
# API SCHEMAS
# =========================================================

class TicketCreate(BaseModel):
    email: EmailStr
    message: str


class TicketReply(BaseModel):
    message: str


class AdminAction(BaseModel):
    action: str  # approve | edit | reject | reassign
    response: Optional[str] = None
    new_intent: Optional[str] = None
    
    
# -----------------------------
# 1️⃣ System prompts for AI Agents
# -----------------------------
TECH_SUPPORT_SYSTEM = """
You are a senior technical support engineer.
Give clear, step-by-step solutions.
"""

BILLING_SUPPORT_SYSTEM = """
You are a billing support specialist.
Handle refunds, invoices, and payment issues professionally.
"""

GENERAL_SUPPORT_SYSTEM = """
You are a customer support agent.
Be polite, concise, and helpful.
"""

# Fallback general system
SUPPORT_SYSTEM = GENERAL_SUPPORT_SYSTEM

# -----------------------------
# 2️⃣ Map intents to prompts (AGENTS dictionary)
# -----------------------------
AGENTS = {
    "technical": TECH_SUPPORT_SYSTEM,
    "billing": BILLING_SUPPORT_SYSTEM,
    "general": GENERAL_SUPPORT_SYSTEM
}
    

# =========================================================
# GUEST APIs
# =========================================================

@app.post("/tickets")
def create_ticket(payload: TicketCreate):
    dup, dup_id = is_duplicate(payload.email, payload.message)
    if dup:
        return {"duplicate": True, "ticket_id": dup_id}

    intent, confidence, level, reasoning = classify_ticket(payload.message)
    action = routing_action(confidence)

    ticket_id = str(uuid.uuid4())
    ticket = {
        "id": ticket_id,
        "guest_email": payload.email,
        "message": payload.message,
        "intent": intent,
        "confidence": confidence,
        "confidence_level": level,
        "status": "processing",
        "admin_required": action != "auto_respond",
        "created_at": datetime.now(UTC).isoformat(),
        "response": None,
        "reasoning": reasoning,
        "error": None
    }

    if action == "admin_only":
        ticket["status"] = "admin_queue"
        TICKETS[ticket_id] = ticket
        return ticket

    try:
        result = agent_response(AGENTS[intent], payload.message)
        ticket["response"] = result["response"]

        if action == "auto_respond":
            ticket["status"] = "sent"
        else:
            ticket["status"] = "pending_admin"

    except Exception as e:
        ticket["status"] = "escalated"
        ticket["error"] = str(e)
        ticket["admin_required"] = True

    TICKETS[ticket_id] = ticket
    return ticket

@app.get("/tickets/{ticket_id}")
def view_ticket(ticket_id: str):
    if ticket_id not in TICKETS:
        raise HTTPException(404, "Ticket not found")
    return TICKETS[ticket_id]

@app.post("/tickets/{ticket_id}/reply")
def reply_ticket(ticket_id: str, payload: TicketReply):
    t = TICKETS.get(ticket_id)
    if not t:
        raise HTTPException(404)
    t["message"] += f"\n\nGuest Reply: {payload.message}"
    t["status"] = "reopened"
    return {"status": "reply received"}

# =========================================================
# ADMIN APIs
# =========================================================

@app.get("/admin/queue")
def admin_queue():
    return [t for t in TICKETS.values() if t["admin_required"]]

@app.post("/admin/ticket/{ticket_id}")
def admin_action(ticket_id: str, payload: AdminAction):
    t = TICKETS.get(ticket_id)
    if not t:
        raise HTTPException(404)

    if payload.action == "approve":
        t["status"] = "sent"
        t["admin_required"] = False

    elif payload.action == "edit":
        t["response"] = payload.response
        t["status"] = "sent"
        t["admin_required"] = False

    elif payload.action == "reject":
        t["status"] = "manual_reply"

    elif payload.action == "reassign":
        t["intent"] = payload.new_intent
        result = agent_response(AGENTS[payload.new_intent], t["message"])
        t["response"] = result["response"]
        t["status"] = "sent"
        t["admin_required"] = False

    else:
        raise HTTPException(400, "Invalid action")

    return {"status": "updated"}
