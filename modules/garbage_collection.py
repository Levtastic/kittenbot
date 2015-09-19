import gc

def init():
    GarbageCollection()

class GarbageCollection():
    auth_commands = {
        'collect_garbage': 90,
    }
    command_descriptions = {
        'collect_garbage': """
            Runs gc.collect() and prints information
            to the console about what was collected
            Syntax: dump_memory
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
        
        if command == 'collect_garbage':
            gc.collect()
            for obj in gc.garbage:
                print('%s\n  %s' % (type(obj), str(x)[:80]))
            
            bot.send(connection, reply_target, bot.db.get_random('yes'), event)
            return True
        
        return False
