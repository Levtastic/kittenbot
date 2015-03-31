import collections, re

def init():
	BanWord()

class BanWord():
	auth_commands = {
		'banword': 50,
		'unbanword': 50,
	}
	command_descriptions = {
		'banword': """
			Sets a new (case insensitive) banned word
			Banned words cause the speaker to be immediately kicked with a variable length ban
			[minutes] defaults to 5 if omitted
			Syntax: banword [minutes] [word]
		""",
		'unbanword': """
			Removes a (case insensitive) banned word
			Banned words cause the speaker to be immediately kicked with a variable length ban
			Syntax: unbanword [word]
		""",
	}
	
	def __init__(self):
		event_handler.hook('modulehandler:before_init_modules', self.on_before_init_modules)
		event_handler.hook('modulehandler:after_load_modules', self.on_after_load_modules)
		
		event_handler.hook('help:get_command_description', self.get_command_description)
		event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
		event_handler.hook('commands:do_auth_command', self.do_auth_command)
		
		event_handler.hook('messages:on_handle_messages', self.on_handle_messages)
		
		self.banned_words = collections.defaultdict(dict)
		self.banned_patterns = {}
	
	def on_before_init_modules(self, module_handler, bot, event_handler, first_time):
		bot.module_parameters['banword:banned_words'] = self.banned_words
	
	def on_after_load_modules(self, module_handler, bot, event_handler, first_time):
		self.banned_words = bot.module_parameters.pop('banword:banned_words', collections.defaultdict(dict))
	
	def get_command_description(self, bot, command):
		if command in self.command_descriptions:
			return self.command_descriptions[command]
	
	def get_auth_commands(self, bot):
		return self.auth_commands
	
	def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
		if command not in self.auth_commands:
			return False # not for us
		
		parameters = parameters.strip()
		
		if command in ('banword', 'unbanword'):
			if reply_target[0] != '#':
				return False # not allowed in private
			
			if not parameters:
				words = list(self.banned_words[reply_target])
				if not words:
					return False
				
				for line in bot.helpers.list_split(words, 10):
					bot.send(connection, reply_target, ', '.join(line), event, False)
				
				return True
		
		if command == 'banword':
			split = parameters.split(' ', 1)
			
			try:
				minutes, word = float(split[0]), split[1]
			except (ValueError, IndexError):
				minutes, word = 5.0, parameters
			
			self.banned_words[reply_target][word.lower()] = minutes
			self.banned_patterns.pop(reply_target, None)
			
			bot.send(connection, reply_target, bot.db.get_random('yes'), event)
			return True
		
		elif command == 'unbanword':
			try:
				del self.banned_words[reply_target][parameters.lower()]
			except KeyError:
				return False
			
			if len(self.banned_words[reply_target]) == 0:
				del self.banned_words[reply_target]
			
			self.banned_patterns.pop(reply_target, None)
			
			bot.send(connection, reply_target, bot.db.get_random('yes'), event)
			return True
		
		return False
	
	def on_handle_messages(self, bot, connection, event, message, is_public, is_action, reply_target, auth_level):
		# if no banned words in this channel, drop out
		if reply_target not in self.banned_words:
			return False
		
		# if we're not op in this channel, drop out
		if not bot.channels[reply_target].is_oper(connection.get_nickname()):
			return False
		
		# if the person speaking *is* op in this channel, drop out
		if bot.channels[reply_target].is_oper(event.source.nick):
			return False
		
		# make the pattern if it doesn't exist
		if not reply_target in self.banned_patterns:
			self.banned_patterns[reply_target] = re.compile(
				r'.*\b(%s)\b.*' % '|'.join(re.escape(word) for word in self.banned_words[reply_target].keys()),
				re.IGNORECASE
			)
		
		# see if we match any banned words
		match = self.banned_patterns[reply_target].match(message)
		if match:
			word = match.group(1)
			
			bot.send(connection, reply_target, bot.db.get_random('kick'), event)
			
			# if there are minutes, set ban
			minutes = float(self.banned_words[reply_target][word.lower()])
			if minutes > 0:
				connection.mode(reply_target, '+b *!%s' % event.source.userhost)
				
				# set unban in future
				connection.execute_delayed(
					minutes * 60,
					lambda: connection.mode(reply_target, '-b *!%s' % event.source.userhost)
				)
				
				reply_prefix = '%g minute ban' % minutes
			
			else:
				reply_prefix = 'Kicked'
			
			connection.kick(reply_target, event.source.nick, '%s for saying "%s"' % (reply_prefix, word))
			
			return True
		
		return False
