import logging

def init():
    Help()

class Help():
    auth_commands = {}
    command_descriptions = {
        'help': """
            Gives information on various commands.
            If no command is given, lists all known commands for the current user's access level.
            Syntax: help [command]
        """,
    }
    
    def __init__(self):
        event_handler.hook('modulehandler:after_load_modules', self.on_after_load_modules)
        
        event_handler.hook('help:get_command_description', self.get_command_description)
        
        event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
        event_handler.hook('commands:do_auth_command', self.do_auth_command)
    
    def on_after_load_modules(self, module_handler, bot, event_handler, first_time):
        self.auth_commands['help'] = min(self.list_auth_commands(bot).values())
    
    def list_auth_commands(self, bot):
        auth_commands = {}
        for result in event_handler.fire('commands:get_auth_commands', bot):
            if result:
                auth_commands.update(result)
        
        return auth_commands
    
    def get_command_description(self, bot, command):
        if command in self.command_descriptions:
            return self.command_descriptions[command]
    
    def get_auth_commands(self, bot):
        return self.auth_commands
    
    def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
        if command not in self.auth_commands:
            return False # not for us
        
        if command == 'help':
            reply_target = event.source.nick
            
            if not parameters:
                commands = []
                for command, command_auth_level in self.list_auth_commands(bot).items():
                    if command_auth_level <= auth_level:
                        commands.append(command)
                
                if commands:
                    commands.sort()
                    for i in range(0, len(commands), 10):
                        bot.send(
                            connection,
                            reply_target,
                            ', '.join(str(key) for key in commands[i:i+10]),
                            event,
                            False
                        )
                    
                    bot.send(connection, reply_target, 'Use "help [command]" for more information on a specific command', event)
                    return True
            
            else:
                parameters = parameters.strip()
                handled = False
                
                command_aliases = {k.strip().lower(): v.strip().lower() for k, v in (v.split('=', 1) for v in bot.db.get_all('command_alias', '%=%'))}
                if parameters in command_aliases:
                    parameters = command_aliases[parameters]
                
                commands = self.list_auth_commands(bot)
                if parameters in commands and commands[parameters] > auth_level:
                    return False
                
                aliases = [a for a, c in command_aliases.items() if c == parameters]
                if aliases:
                    bot.send(connection, reply_target, 'Command aliases: ' + ', '.join([parameters] + aliases), event, False)
                    handled = True
                
                description = [r for r in event_handler.fire('help:get_command_description', (bot, parameters)) if r]
                if description:
                    description = description[0]
                    
                    for line in [l.strip() for l in description.split('\n') if l.strip()]:
                        bot.send(connection, reply_target, line, event, False)
                    
                    handled = True
                
                return handled
        
        return False
    
    def get_description(self, bot, command):
        auth_commands = {}
        
        for result in event_handler.fire('help:get_command_description', (bot, command)):
            if result:
                return result
        
        return auth_commands
