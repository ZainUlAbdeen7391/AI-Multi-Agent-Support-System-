from models import Ticket
from core.orchestrator import OrchestratorAI
from agents.refund import RefundAgent
from agents.technical import TechnicalAgent
from agents.general import GeneralAgent


class TicketService:
    def __init__(self, client):
        self.orchestrator = OrchestratorAI(client)
        self.agents = {
            "refund": RefundAgent(client),
            "technical": TechnicalAgent(client),
            "general": GeneralAgent(client),
        }

    def process(self, message, email):
        ticket = Ticket.create(message, email)

        intent, conf, level = self.orchestrator.classify(message)
        ticket.intent = intent
        ticket.confidence = conf

        if level == "low":
            ticket.admin_required = True
            return ticket

        agent = self.agents[intent]
        try:
            result = agent.respond(ticket)
            ticket.response = result["response"]
            ticket.status = "sent" if level == "high" else "pending_admin"
            ticket.admin_required = level != "high"
        except Exception as e:
            ticket.error = str(e)
            ticket.admin_required = True

        return ticket
