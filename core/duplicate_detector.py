def is_duplicate(new_message, tickets):
    for t in tickets:
        if t.message.lower() in new_message.lower():
            return True, t.id
    return False, None
