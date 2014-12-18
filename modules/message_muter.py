def init():
	MessageMuter()

class MessageMuter():
	auth_commands = {
		'mute': 0,
		'unmute': 0,
	}
	command_descriptions = {
		'mute': """
			Stops the bot talking in the current channel
			Undo this with the "unmute" command
			Syntax: mute
		""",
		'unmute': """
			Lets the bot talk in the current channel again
			Syntax: unmute
		""",
	}
	
	def __init__(self):
		self.last_mute = ''
		
		event_handler.hook('help:get_command_description', self.get_command_description)
		
		event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
		event_handler.hook('commands:do_auth_command', self.do_auth_command)
		
		event_handler.hook('bot:on_before_send_message', self.on_before_send_message)
	
	def get_command_description(self, bot, command):
		if command in self.command_descriptions:
			return self.command_descriptions[command]
	
	def get_auth_commands(self, bot):
		return self.auth_commands
	
	def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
		if command not in self.auth_commands:
			return False # not for us
		
		if event.target[0] == '#':
			# mute in the channel we were told to hush
			channel = event.target
		else:
			# or maybe they don't want the bot to PM them, or something
			channel = event.source.nick
		
		if command == 'mute' and bot.db.add('muted_targets|' + bot.server_name, channel):
			self.last_mute = channel
			bot.send(connection, reply_target, bot.db.get_random('yes'), event)
			return True
		
		elif command == 'unmute' and bot.db.delete('muted_targets|' + bot.server_name, channel):
			bot.send(connection, reply_target, bot.db.get_random('yes'), event)
			return True
		
		return False
	
	def on_before_send_message(self, bot, connection, target, message, event):
		if target == self.last_mute:
			self.last_mute = ''
			return True
		
		if target.lower() in bot.db.get_all('muted_targets|' + bot.server_name):
			return False
