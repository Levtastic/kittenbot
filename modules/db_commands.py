import logging
import re

def init():
	DbCommands()

class DbCommands():
	auth_commands = {
		'add': 30, # unless adding non-messages, in which case 70
		'list': 30,
		'remove': 30,
		'set': 70,
		'sql': 90,
	}
	
	def __init__(self):
		event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
		event_handler.hook('commands:do_auth_command', self.do_auth_command)

	def get_auth_commands(self, bot, connection, event, command, parameters, reply_target, auth_level):
		return self.auth_commands

	def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
		if command not in self.auth_commands:
			return False # not for us
		
		if command == 'add': # ResponseBot: *pokes ResponseBot = *bites !speaker
			try:
				key, value = [s.strip() for s in parameters.strip().split('=', 1)]
			except ValueError:
				return False
			
			key = self.process_input(connection, key, True, auth_level, False)
			value = self.process_input(connection, value, False, auth_level, False)
			
			if key is False or value is False:
				return False
			
			if bot.db.add(key, value):
				bot.send(connection, reply_target, bot.db.get_random('yes'), event)
				return True
		
		elif command == 'remove': # ResponseBot: remove *pokes ResponseBot = *bites%
			try:
				key, value = [s.strip() for s in parameters.strip().split('=', 1)]
			except ValueError:
				key = parameters
				value = ''
			
			key = self.process_input(connection, key, True, auth_level, True)
			value = self.process_input(connection, value, False, auth_level, True)
			
			if key is False or value is False:
				return False
			
			if bot.db.delete(key, value):
				bot.send(connection, reply_target, bot.db.get_random('yes'), event)
				return True
		
		elif command == 'list': # ResponseBot: list 2 *pokes ResponseBot = *bites%
			results_per_page = 5
			page = 1
			
			param_split = parameters.strip().split(' ', 1)
			if param_split[0].isdigit():
				page = int(parameters[0])
				parameters = param_split[1]
			
			try:
				key, value = [s.strip() for s in parameters.strip().split('=', 1)]
			except ValueError:
				key = parameters.strip()
				value = ''
			
			key = self.process_input(connection, key, True, auth_level, True)
			value = self.process_input(connection, value, False, auth_level, True)
			
			if key is False or value is False:
				return False
			
			results = bot.db.list(results_per_page, page, value, key, auth_level < 70)
			
			if results:
				connection.privmsg(reply_target, 'Results page %d:' % page)
				
				for result in results:
					connection.privmsg(reply_target, ' | '.join(str(r) for r in result))
				return True
		
		elif command == 'set': # ResponseBot: set nickname = Name1, Name2, Name3, Name4
			try:
				key, value = [s.strip() for s in parameters.strip().split('=', 1)]
			except ValueError:
				return False
			
			values = [s.strip() for s in value.split(',')]
			if not values:
				return False
			
			if bot.db.set(key, values):
				bot.send(connection, reply_target, bot.db.get_random('yes'), event)
				return True
		
		elif command == 'sql': # ResponseBot: sql force SELECT * FROM vars WHERE key LIKE '%fish%'
			try:
				force, command = [s.strip() for s in parameters.strip().split(' ', 1)]
			except ValueError:
				return False
			else:
				force = force.replace('-', '').replace('/', '').replace('\\', '')
				if force in ('force', 'f') and bot.db.sql(connection, reply_target, command):
					bot.send(connection, reply_target, bot.db.get_random('yes'), event)
					return True
		
		return False
	
	def process_input(self, connection, message, allow_tilde, auth_level, wildcard):
		if not message:
			return message
		
		ordered_message = self.order_message_type_codes(message, allow_tilde)
		if not ordered_message and auth_level < 70:
			return False
		
		message = ordered_message or message
		
		if ordered_message:
			for name in [connection.get_nickname()] + bot.db.get_all('nick_alias'):
				message = re.sub(re.escape(name), '!me', message, flags = re.IGNORECASE)
		
		if wildcard:
			message = message and '%' + message + '%'
		
		return message

	def order_message_type_codes(self, message, allow_tilde):
		allowed_codes = allow_tilde and ('-', '*', '~') or ('-', '*')
		message_type_matches = []
		
		for c in message:
			if c in allowed_codes and c not in message_type_matches:
				message_type_matches.append(c)
			else:
				break
		else:
			return False
		
		if not message_type_matches:
			return False
		
		message = message[message.index(message_type_matches[-1])+1:]
		
		if message_type_matches == ['~']:
			message_type_matches += ['-', '*']
		
		# make sure the message codes are in the right order
		codes = ''
		for code in ('~', '-', '*'):
			if code in message_type_matches:
				codes += code
		
		if not codes:
			return False
		
		return codes + message
