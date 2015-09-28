def init():
    event_handler.hook('send:on_before_send_message', on_before_send_message)

def on_before_send_message(bot, connection, target, message, event, process_message):
    max_message_length = int(bot.db.get('max_message_length', default_value = 450))
    if len(message) <= max_message_length:
        return True
    
    pieces = [''.join(piece) for piece in zip(*[iter(message)] * max_message_length)]
    left_over = len(message) % max_message_length
    if left_over:
        pieces.append(message[-left_over:])
    
    for piece in pieces:
        bot.send(connection, target, piece, event, process_message)
    
    return False
