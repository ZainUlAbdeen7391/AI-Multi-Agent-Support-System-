import time

AGENT_TIMEOUT = 1800  

def check_timeout(ticket):
    if ticket.status == "processing":
        ticket.status = "escalated"
        ticket.admin_required = True
