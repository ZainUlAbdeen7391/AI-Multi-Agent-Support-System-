def admin_review(ticket, action, edited_response=None):
    if action == "approve":
        ticket.status = "sent"
    elif action == "edit":
        ticket.response = edited_response
        ticket.status = "sent"
    elif action == "reject":
        ticket.status = "manual_reply"
    elif action == "reassign":
        ticket.status = "reassigned"
    return ticket
