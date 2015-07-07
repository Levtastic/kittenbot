import logging, re

def init():
    AdminMessage()

class AdminMessage():
    auth_commands = {
        'admin_message': 80,
    }
    command_descriptions = {
        'admin_message': """
            Stores a message to be sent later when someone is around
            [message] will be sent in private to the first person seen talking whose hostmask matches [regex]
            Syntax: admin_message [regex] [message]
        """,
    }
    
    def __init__(self):
        event_handler.hook('modulehandler:before_init_modules', self.on_before_init_modules)
        event_handler.hook('modulehandler:after_load_modules', self.on_after_load_modules)
        
        event_handler.hook('help:get_command_description', self.get_command_description)
        
        event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
        event_handler.hook('commands:do_auth_command', self.do_auth_command)
        
        event_handler.hook('messages:on_handle_messages', self.on_handle_messages, -1)
        
        self.messages = []
    
    def on_before_init_modules(self, module_handler, bot, event_handler, first_time):
        bot.module_parameters['admin_message:messages'] = self.messages
    
    def on_after_load_modules(self, module_handler, bot, event_handler, first_time):
        self.messages = bot.module_parameters.pop('admin_message:messages', self.messages)
    
    def get_command_description(self, bot, command):
        if command in self.command_descriptions:
            return self.command_descriptions[command]
    
    def get_auth_commands(self, bot):
        return self.auth_commands
    
    def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
        if command not in self.auth_commands:
            return False # not for us
        
        if command == 'admin_message':
            try:
                regex, message = parameters.strip().split(' ', 1)
                re.compile(regex)
            except BaseException:
                return False
            
            message = message.strip()
            
            if not message:
                return False
            
            self.messages.append((regex, message))
            
            bot.send(connection, reply_target, bot.db.get_random('yes'), event)
            return True
        
        return False
    
    def on_handle_messages(self, bot, connection, event, message, is_public,
                                is_action, reply_target, auth_level):
        for message in self.messages[:]:
            if re.match(message[0], str(event.source)):
                logging.info('"%s" message sent to %s' % (
                    message[1],
                    event.source,
                ))
                bot.send(connection, event.source.nick, message[1], event)
                self.messages.remove(message)
        
        return False
