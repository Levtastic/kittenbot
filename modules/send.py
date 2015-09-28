import types, logging

def init():
    bot.send = types.MethodType(send, bot)

def send(self, connection, target, message, event = None, process_message = True):
    if any(result is False for result in self.module_handler.fire_event('send:on_before_send_message', (self, connection, target, message, event, process_message))):
        return False
    
    if process_message:
        for process_function in self.module_handler.get_event_handlers('send:on_process_message'):
            try:
                message = process_function(self, message, connection, event, target)
            except BaseException as e:
                error = 'error in message processing function: %s: %s' % (type(e).__name__, e)
                logging.exception(error)
                print(error)
    
    if not message or not isinstance(message, str):
        return False
    
    sent_by_module = True
    if not any(result is True for result in self.module_handler.fire_event('send:on_send_message', (self, connection, target, message, event, process_message))):
        try:
            # default behaviour, if nothing has overridden it
            connection.privmsg(target, message)
            sent_by_module = False
        except BaseException as e:
            error = 'unable to send "%s" to %s: %s: %s' % (message, target, type(e).__name__, e)
            logging.exception(error)
            print(error)
            return False
    
    self.module_handler.fire_event('send:on_after_send_message', (self, connection, target, message, event, sent_by_module))
    
    return True
