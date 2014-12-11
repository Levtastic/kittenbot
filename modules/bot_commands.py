import logging

def init():
	BotCommands()

class BotCommands():
	auth_commands = {
		'nick': 60,
		'die': 80,
		'reload': 80,
		'eval': 90,
	}
	
	def __init__(self):
		event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
		event_handler.hook('commands:do_auth_command', self.do_auth_command)

	def get_auth_commands(self, bot, connection, event, command, parameters, reply_target, auth_level):
		return self.auth_commands

	def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
		if command not in self.auth_commands:
			return False # not for us
		
		if command == 'nick': # ResponseBot: nick BotResponder
			if not parameters:
				nicklist = bot.db.get_all('nickname|' + bot.server_name)
				if nicklist:
					connection.nick(nicklist[0])
			else:
				connection.nick(parameters.strip())
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
		
		elif command == 'eval': # ResponseBot: eval force connection.ping('ResponseBot')
			try:
				force, command = [s.strip() for s in parameters.strip().split(' ', 1)]
			except ValueError:
				return False
			else:
				force = force.replace('-', '').replace('/', '').replace('\\', '')
				if force in ('force', 'f'):
					try:
						eval(command)
					except BaseException as e:
						connection.privmsg(reply_target, '%s %s' % (str(type(e)), str(e)))
						return False
					else:
						bot.send(connection, reply_target, bot.db.get_random('yes'), event)
						return True
		
		return False
