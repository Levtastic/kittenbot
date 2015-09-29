def init():
    event_handler.hook('send:on_before_send_message', on_before_send_message)

def on_before_send_message(bot, connection, target, message, event, process_message):
    max_message_length = int(bot.db.get('max_message_length', default_value = 400))
    if len(message) <= max_message_length and '\n' not in message:
        return True
    
    for message in message.split('\n'):
        for i in range(0, len(message), max_message_length):
            bot.send(
                connection,
                target,
                message[i:i+max_message_length],
                event,
                process_message
            )
    
    return False
