import re

def init():
	Ignore()

class Ignore():
	auth_commands = {
		'ignore': 40,
		'unignore': 40,
	}
	command_descriptions = {
		'ignore': """
			Stops the bot listening to someone based on a regex match of their host string
			Example host string: Nickname!~RealName@127.0.0.1
			Syntax: ignore [hostmask regex]
		""",
		'unignore': """
			Removes a pattern from the hostmask ignore list
			Note: Use "list ignore_host|" for a list of current ignore patterns
			Syntax: unignore [hostmask regex]
		""",
	}
	
	def __init__(self):
		event_handler.hook('help:get_command_description', self.get_command_description)
		
		event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
		event_handler.hook('commands:do_auth_command', self.do_auth_command)
		
		event_handler.hook('messages:on_before_handle_messages', self.on_before_handle_messages)
	
	def get_command_description(self, bot, command):
		if command in self.command_descriptions:
			return self.command_descriptions[command]
	
	def get_auth_commands(self, bot):
		return self.auth_commands
	
	def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
		if command not in self.auth_commands:
			return False # not for us
		
		parameters = parameters.strip()
		
		if not parameters:
			return False
		
		if command == 'ignore':
			try:
				re.compile(parameters)
			except BaseException:
				return False
			
			if bot.db.add('ignore_host|' + bot.server_name, parameters):
				bot.send(connection, reply_target, bot.db.get_random('yes'), event)
				return True
		
		elif command == 'unignore' and bot.db.delete('ignore_host|' + bot.server_name, parameters):
			bot.send(connection, reply_target, bot.db.get_random('yes'), event)
			return True
		
		return False
	
	def on_before_handle_messages(self, bot, connection, event, message, is_public, is_action, reply_target, auth_level):
		for regex in bot.db.get_all('ignore_host|' + bot.server_name):
			if re.match(regex, str(event.source)):
				return False
