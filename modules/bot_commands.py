import logging

def init():
	BotCommands()

class BotCommands():
	auth_commands = {
		'commands': 0,
		'nick': 60,
		'die': 80,
		'reload': 80,
		'exec': 90,
	}
	
	def __init__(self):
		event_handler.hook('modulehandler:after_load_modules', self.on_after_load_modules)
		
		event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
		event_handler.hook('commands:do_auth_command', self.do_auth_command)
	
	def on_after_load_modules(self, module_handler, bot, event_handler, first_time):
		self.auth_commands['commands'] = min(bot.helpers.get_auth_commands(bot).values())
	
	def get_auth_commands(self, bot):
		return self.auth_commands
	
	def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
		if command not in self.auth_commands:
			return False # not for us
		
		if command == 'commands':
			commands = []
			for command, command_auth_level in bot.helpers.get_auth_commands(bot).items():
				if command_auth_level <= auth_level:
					commands.append(command)
			
			if commands:
				commands.sort()
				for line in bot.helpers.list_split(commands, 10):
					bot.send(connection, reply_target, '-' + ', '.join(str(key) for key in line), event)
				
				return True
		
		elif command == 'nick': # ResponseBot: nick BotResponder
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
						bot.send(connection, reply_target, '-%s: %s' % (type(e).__name__, str(e)), event)
					else:
						bot.send(connection, reply_target, bot.db.get_random('yes'), event)
					
					return True
		
		return False
