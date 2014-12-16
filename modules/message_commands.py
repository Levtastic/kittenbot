import logging

def init():
	MessageCommands()

class MessageCommands():
	auth_commands = {
		'send': 60,
		'say': 60,
		'do': 60,
	}
	
	def __init__(self):
		event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
		event_handler.hook('commands:do_auth_command', self.do_auth_command)

	def get_auth_commands(self, bot):
		return self.auth_commands

	def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
		if command not in self.auth_commands:
			return False # not for us
		
		if command == 'send': # ResponseBot: send message #responsebot -Hello world!
			try:
				channel, message_text = parameters.strip().split(' ', 1)
			except ValueError:
				pass
			else:
				if channel[0] != '#' or channel.lower() in bot.channels:
					bot.send(connection, channel, message_text, event)
					bot.send(connection, reply_target, bot.db.get_random('yes'), event)
					return True
		
		elif command == 'say': # ResponseBot: say #responsebot Hello World!
			try:
				channel, message_text = parameters.strip().split(' ', 1)
			except ValueError:
				pass
			else:
				if channel[0] != '#' or channel.lower() in bot.channels:
					bot.send(connection, channel.lower(), '- ' + message_text, event)
					bot.send(connection, reply_target, bot.db.get_random('yes'), event)
					return True
		
		elif command == 'do': # ResponseBot: do #responsebot dances!
			try:
				channel, message_text = parameters.strip().split(' ', 1)
			except ValueError:
				pass
			else:
				if channel[0] != '#' or channel.lower() in bot.channels:
					bot.send(connection, channel.lower(), '* ' + message_text, event)
					bot.send(connection, reply_target, bot.db.get_random('yes'), event)
					return True
		
		return False
