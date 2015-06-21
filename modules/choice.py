import random

def init():
    Choose()

class Choose():
    auth_commands = {
        'choose': 0,
    }
    command_descriptions = {
        'choose': """
            Picks randomly between multiple options
            Syntax: choose [option 1] or [option 2] [or [option 3] [...]]
        """,
    }
    
    def __init__(self):
        event_handler.hook('help:get_command_description', self.get_command_description)
        
        event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
        event_handler.hook('commands:do_auth_command', self.do_auth_command)
    
    def get_command_description(self, bot, command):
        if command in self.command_descriptions:
            return self.command_descriptions[command]
    
    def get_auth_commands(self, bot):
        return self.auth_commands
    
    def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
        if command not in self.auth_commands:
            return False # not for us
        
        if command == 'choose':
            options = [self.process_option(s) for s in parameters.split(' or ')]
            options = [option for option in options if option]
            options = list(set(options))
            
            if len(options) < 2 and options[0].lower() != '!someone':
                return False
            
            message_template = bot.db.get('choice_reply_template', default_value = '%(choice)s')
            
            bot.send(connection, reply_target, message_template % {'choice': random.choice(options)}, event)
            
            return True
    
    def process_option(self, option):
        option = option.strip()
        
        if option[-1] == ',':
            option = option[:-1].strip()
        
        return option
