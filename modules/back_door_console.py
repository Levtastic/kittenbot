from modules.resources.async_input import AsyncInput
from irc.client import Event, NickMask
import logging, datetime

def init():
    BackDoorConsole()

class BackDoorConsole():
    def __init__(self):
        self.run = False
        
        bot.ai = AsyncInput(prefix = '%s > ' % bot.server_name)
        bot.ai.start(False)
        
        event_handler.hook('modulehandler:before_init_modules', self.on_before_init_modules)
        event_handler.hook('modulehandler:after_load_modules', self.on_after_load_modules)
        
        event_handler.hook('send:on_send_message', self.on_send_message)
    
    def on_before_init_modules(self, module_handler, bot, event_handler, first_time):
        if hasattr(bot, 'ai'):
            bot.ai.stop()
        
        self.run = False
    
    def on_after_load_modules(self, module_handler, bot, event_handler, first_time):
        self.run = True
        self.command_loop(bot, event_handler)
    
    def command_loop(self, bot, event_handler):
        if not self.run:
            return
        
        command = bot.ai.get(False)
        
        if command:
            connection = bot.connection # for now - in future, able to tab between connections?
            
            if command[:4] == '/me ':
                event_type = 'action'
                command = command[4:]
            
            else:
                event_type = 'privmsg'
            
            # we use -CONSOLE as a reference to the console because the IRC spec doesn't allow
            # nicknames with "-" as the first character, so we know this won't be a real nick
            event = Event(
                type = event_type,
                source = NickMask('-CONSOLE'),
                target = connection.get_nickname(),
                arguments = (command, )
            )
            
            handled = False
            
            for process_function in event_handler.get_handlers('console:on_input'):
                try:
                    if process_function(bot, connection, event, command) is True:
                        handled = True
                        break
                
                except BaseException as e:
                    error = 'error in console processing function: %s: %s' % (type(e).__name__, e)
                    logging.exception(error)
                    print(error)
            
            if not handled:
                try:
                    exec(command)
                
                except BaseException as e:
                    print('%s: %s' % (type(e).__name__, str(e)))
            
        bot.ai.ready()
        
        bot.execute_delayed(bot.connection, 1, self.command_loop, (bot, event_handler))
    
    def on_send_message(self, bot, connection, target, message, event, process_message):
        if target == '-CONSOLE':
            if process_message:
                if message[0] == '-':
                    message = '- %s' % message[1:]
                
                elif message[0] == '*':
                    message = '* %s' % message[1:]
            
            message = '[%s] %s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), message)
            
            print(message)
            return True
        
        return False
