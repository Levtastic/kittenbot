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
		self.auth_commands['help'] = min(bot.helpers.get_auth_commands(bot).values())
	
	def get_command_description(self, bot, command):
		if command in self.command_descriptions:
			return self.command_descriptions[command]
	
	def get_auth_commands(self, bot):
		return self.auth_commands
	
	def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
		if command not in self.auth_commands:
			return False # not for us
		
		if command == 'help':
			if not parameters:
				commands = []
				for command, command_auth_level in bot.helpers.get_auth_commands(bot).items():
					if command_auth_level <= auth_level:
						commands.append(command)
				
				if commands:
					commands.sort()
					for line in bot.helpers.list_split(commands, 10):
						bot.send(connection, reply_target, '-' + ', '.join(str(key) for key in line), event)
					
					bot.send(connection, reply_target, '-Use "help [command]" for more information on a specific command', event)
					return True
			
			else:
				parameters = parameters.strip()
				handled = False
				
				command_aliases = bot.helpers.get_command_aliases(bot)
				if parameters in command_aliases:
					parameters = command_aliases[parameters]
				
				aliases = [a for a, c in bot.helpers.get_command_aliases(bot).items() if c == parameters]
				if aliases:
					bot.send(connection, reply_target, '-Command aliases: ' + ', '.join([parameters] + aliases), event, False)
					handled = True
				
				description = [r for r in event_handler.fire('help:get_command_description', (bot, parameters)) if r]
				if description:
					description = description[0]
					
					for line in [l.strip() for l in description.split('\n') if l.strip()]:
						bot.send(connection, reply_target, '-' + line, event, False)
					
					handled = True
				
				return handled
		
		return False
	
	def get_description(self, bot, command):
		auth_commands = {}
		
		for result in event_handler.fire('help:get_command_description', (bot, command)):
			if result:
				return result
		
		return auth_commands
