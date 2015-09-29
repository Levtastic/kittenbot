def init():
    bot.helpers = Helpers()

class Helpers():
    def get_auth_commands(self, bot):
        auth_commands = {}
        
        for result in event_handler.fire('commands:get_auth_commands', bot):
            if result:
                auth_commands.update(result)
        
        return auth_commands
