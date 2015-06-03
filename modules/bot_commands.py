import logging

def init():
    BotCommands()

class BotCommands():
    auth_commands = {
        'nick': 60,
        'die': 80,
        'reload': 80,
        'exec': 90,
    }
    command_descriptions = {
        'nick': """
            Sets the bot to a new nickname
            If no nickname is given, tells the bot to return to its most ideal nickname
            Syntax: nick [nickname]
        """,
        'die': """
            Shuts down the bot.
            Note: The bot will not automatically restart after this command is given.
            Syntax: die [quit message]
        """,
        'reload': """
            Recompiles bot source files from disk and reloads module event hooks
            If unsuccessful, reverts changes
            Syntax: reload
        """,
        'exec': """
            Runs arbitrary python code. Obviously, be careful with this.
            Syntax: exec -force [executable python code]
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
        
        if command == 'nick': # ResponseBot: nick BotResponder
            if not parameters:
                nicklist = bot.db.get_all('nickname|' + bot.server_name)
                if nicklist and connection.get_nickname() != nicklist[0]:
                    connection.nick(nicklist[0])
                    bot.send(connection, reply_target, bot.db.get_random('yes'), event)
                    return True
            else:
                connection.nick(parameters)
                bot.send(connection, reply_target, bot.db.get_random('yes'), event)
                return True
        
        elif command == 'die': # ResponseBot: die
            if bot.quit(connection, event, parameters):
                bot.send(connection, reply_target, bot.db.get_random('yes'), event)
                return True
        
        elif command == 'reload': # ResponseBot: reload
            if bot.module_handler.load_modules():
                bot.send(connection, reply_target, bot.db.get_random('yes'), event)
                return True
        
        elif command == 'exec': # ResponseBot: exec force connection.ping('ResponseBot')
            try:
                force, command = [s.strip() for s in parameters.strip().split(' ', 1)]
            except ValueError:
                return False
            else:
                force = force.replace('-', '').replace('/', '').replace('\\', '')
                if force in ('force', 'f'):
                    try:
                        exec(command)
                    except BaseException as e:
                        bot.send(connection, reply_target, '%s: %s' % (type(e).__name__, str(e)), event, False)
                    else:
                        bot.send(connection, reply_target, bot.db.get_random('yes'), event)
                    
                    return True
        
        return False
