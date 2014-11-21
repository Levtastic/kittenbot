class HelpHandler():
	command_descriptions = {
		'help': 'Provides information on how to use commands', #
		'add': 'Add new items to the database', #
		'list': 'Lists items already present in the database', #
		'remove': 'Removes items from the database. Note: Will only remove if it finds one matching entry in the database', #
		'send': 'Sends messages or actions to a channel or person', #
		'say': 'Sends messages to a channel or person', #
		'do': 'Sends actions to a channel or person', #
		'join': 'Joins a channel temporarily (does not add the channel to the database for future joins)', #
		'part': 'Leaves a channel', #
		'blacklist': 'Stops a channel in the database being automatically joined', #
		'unblacklist': 'Allows a channel in the database to be automatically joined again', #
		'die': 'Shuts down the bot',
		'sql': 'Runs arbitrary SQL on the database. USE WITH EXTREME CAUTION',
	}
	object_descriptions = {
		'completed_command_messages' : 'Sent on the successful completion of a command',
		'unknown_command_messages' : 'Send on an unrecognised or unsuccessful command',
		'random_mentions' : 'Sent on someone mentioning the bot\'s name',
		'random_messages' : 'Sent randomly when the bot is bored',
		'response_messages' : 'Sent in response to a specific action or message being seen by the bot',
		'join_messages' : 'Sent to a channel after joining',
		'part_messages' : 'Sent to a channel before leaving',
		'channels' : 'Channels the bot can auto-join when it wants to',
		'users' : 'Account names for people with access to the bot',
	}
	message_code_descriptions = {
		'!someone': 'A random name from the channel',
		'!channel': 'The name of the current channel',
		'!speaker': 'The name of the person who caused the bot to reply',
		'!me': 'The bot\'s current name',
	}
	
	def __init__(self, auth_commands, command_aliases, table_aliases):
		self.auth_commands = auth_commands
		self.command_aliases = command_aliases
		self.table_aliases = table_aliases
	
	def do_command(self, connection, reply_target, command, auth_level):
		if not command:
			commands = [command for command, auth in self.auth_commands.items() if auth <= auth_level]
			commands.sort()
			connection.privmsg(reply_target, 'Available Commands: ' + ', '.join(commands))
			connection.privmsg(reply_target, 'Use "help [command]" for more information about a specific command.')
			return True
		
		command_split = command.strip().split(' ')
		if len(command_split) == 1:
			command = command_split[0]
			
			if command in self.command_aliases:
				real_command = self.command_aliases[command]
			else:
				real_command = command
			
			if self.auth_commands[real_command] > auth_level:
				return False
			
			aliases = [real_command] + [alias for alias, cmd in self.command_aliases.items() if cmd == real_command]
			aliases.sort()
			if len(aliases) > 1:
				connection.privmsg(reply_target, 'Command aliases: ' + ', '.join(aliases))
			
			if real_command in self.command_descriptions:
				connection.privmsg(reply_target, 'Description: %s' % self.command_descriptions[real_command])
			
			if real_command in ('add', 'remove', 'list'):
				objects = [object for object in self.table_aliases.keys()]
				objects.sort()
				connection.privmsg(reply_target, 'Syntax: %s [object] [parameters]' % command)
				connection.privmsg(reply_target, 'Objects: ' + ', '.join(objects))
				connection.privmsg(reply_target, 'Use "help %s [object]" for more information about a specific command.' % command)
				return True
			
			elif real_command == 'help':
				return True
			
			elif real_command == 'send':
				connection.privmsg(reply_target, 'Syntax: %s [message type] [target] [message]' % command)
				connection.privmsg(reply_target, 'Message Types: message, action')
				connection.privmsg(reply_target, '[target] can be a channel (starting with #) or a person\'s name')
				return True
			
			elif real_command in ('say', 'do'):
				connection.privmsg(reply_target, 'Syntax: %s [target] [message]' % command)
				connection.privmsg(reply_target, '[target] can be a channel (starting with #) or a person\'s name')
				return True
			
			elif real_command == 'join':
				connection.privmsg(reply_target, 'Syntax: %s [channel]' % command)
				return True
			
			elif real_command == 'part':
				connection.privmsg(reply_target, 'Syntax: %s [channel] [message*]' % command)
				connection.privmsg(reply_target, '* Optional')
				return True
			
			elif real_command in ('blacklist', 'unblacklist'):
				connection.privmsg(reply_target, 'Syntax: %s [channel] [reason*]' % command)
				connection.privmsg(reply_target, '* Optional')
				return True
				
			elif real_command == 'die':
				connection.privmsg(reply_target, 'Syntax: %s [message*]' % command)
				connection.privmsg(reply_target, '* Optional')
				return True
				
			elif real_command == 'sql':
				connection.privmsg(reply_target, 'Syntax: %s force [sql command]' % command)
				return True
		
		elif len(command_split) == 2:
			command, object = command_split
			
			if command == 'message' and object == 'codes':
				connection.privmsg(reply_target, 'Message Codes:')
				for code, description in self.message_code_descriptions.items():
					connection.privmsg(reply_target, '%s : %s' % (code, description))
				return True
			
			if command in self.command_aliases:
				real_command = self.command_aliases[command]
			else:
				real_command = command
			
			if self.auth_commands[real_command] > auth_level:
				return False
			
			if real_command not in ('add', 'remove', 'list'):
				return False
			
			if object in self.table_aliases:
				table = self.table_aliases[object]
			elif object[:-1] in self.table_aliases:
				table = self.table_aliases[object[:-1]]
			else:
				return False
			
			connection.privmsg(reply_target, 'Description: %s' % self.object_descriptions[table])
			
			if real_command in ('remove', 'list'):
				connection.privmsg(reply_target, 'Syntax: %s %s [id or search terms]' % (command, object))
				return True
			
			if table == 'response_messages':
				connection.privmsg(reply_target, 'Syntax: %s %s [trigger type] [trigger text] = [response type] [response text]' % (command, object))
				connection.privmsg(reply_target, 'Trigger Types: message, action, both')
				connection.privmsg(reply_target, 'Response Types: message, action')
			
			elif table == 'channels':
				connection.privmsg(reply_target, 'Syntax: %s %s [channel name]' % (command, object))
			
			elif table == 'users':
				connection.privmsg(reply_target, 'Syntax: %s %s [account name] [auth level*]' % (command, object))
				connection.privmsg(reply_target, '* Optional (default 30), and must be lower than your own auth level')
			
			else:
				connection.privmsg(reply_target, 'Syntax: %s %s [message type] [message]' % (command, object))
				connection.privmsg(reply_target, 'Message Types: message, action')
			
			connection.privmsg(reply_target, 'For shortcodes that can be used in messages, type "help message codes"')
			
			return True
		
		return False
