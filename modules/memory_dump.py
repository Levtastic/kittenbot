import sys, gc, inspect

def init():
    MemoryDump()

class MemoryDump():
    auth_commands = {
        'dump_memory': 90,
    }
    command_descriptions = {
        'dump_memory': """
            Dumps a log file to disc about the currently used memory
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
        
        if command == 'dump_memory':
            dump = open("memory.csv", 'w')
            dump.write('ID;Class;File;Size\n')
            for obj in gc.get_objects():
                if hasattr(obj, '__class__'):
                    dump.write('%s;%s;%s;%s\n' % (
                        repr(id(obj)),
                        repr(obj.__class__),
                        repr(inspect.getmodule(obj)),
                        repr(sys.getsizeof(obj, 0)),
                    ))
            
            bot.send(connection, reply_target, bot.db.get_random('yes'), event)
            return True
        
        return False
