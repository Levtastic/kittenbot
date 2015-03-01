import logging

from callbackhandler import CallbackHandler

def init():
	Commands()

class Commands():
	def __init__(self):
		# commands get checked first - other modules shouldn't be able to override commands from happening
		event_handler.hook('messages:on_handle_messages', self.on_handle_message, 0)
		
		event_handler.hook('commands:do_command', self.do_command)
		
		event_handler.hook('irc:on_whoisaccount', self.on_whoisaccount)
		event_handler.hook('irc:on_endofwhois', self.on_endofwhois)
		
		self.callback_handler = CallbackHandler()
	
	def on_handle_message(self, bot, connection, event, message, is_public, is_action, reply_target, auth_level):
		if not is_action:
			command = None
			
			if not is_public:
				command = message.strip()
			else:
				# also try splitting by comma
				# also, allow any of the nick aliases to be after the colon / comma
				message_split = event.arguments[0].split(':', 1)
				if len(message_split) == 2 and message_split[0].lower().strip() == bot.connection.get_nickname().lower():
					command = message_split[1]
			
			# if sent in private message or prefixed by our name, try it as a command
			if command:
				return self.do_command(bot, connection, event, command, reply_target, auth_level)
		
		# if we reach here, we didn't handle this message
		return False
	
	def do_command(self, bot, connection, event, command, reply_target, auth_level):
		original_command = command
		
		try:
			command, parameters = command.strip().split(' ', 1)
		except ValueError:
			command = command
			parameters = ''
		
		command = command.strip().lower()
		
		command_aliases = bot.helpers.get_command_aliases(bot)
		if command in command_aliases:
			command = command_aliases[command]
		
		auth_commands = bot.helpers.get_auth_commands(bot)
		if '=' in parameters and command not in auth_commands:
			parameters = original_command
			command = 'add'
		
		if command in auth_commands:
			if auth_level is None:
				auth_levels = [r for r in event_handler.fire('commands:on_get_auth_level', (bot, connection, event, event.source.nick)) if isinstance(r, int)]
				
				if auth_levels:
					auth_level = max(auth_levels)
				
				else:
					self.callback_handler.add(
						'whois-' + event.source.nick,
						self.repeat_message_event,
						{
							'bot': bot,
							'connection': connection,
							'event': event,
							'auth_level': 0,
						}
					)
					connection.whois(event.source.nick)
					return True # we'll come back when we have more information
			
			logging.info('"%s" command issued by %s (%d) in %s' % (
				event.arguments[0],
				event.source.nick,
				auth_level,
				event.target,
			))
			
			if auth_level >= auth_commands[command]:
				if not any(result is True for result in event_handler.fire('commands:do_auth_command', (bot, connection, event, command, parameters, reply_target, auth_level))):
					bot.send(connection, reply_target, bot.db.get_random('no'), event)
				
				# we've handled the command, whether it failed or not,
				# so we return True to stop any further message processing
				return True
			
			else:
				logging.info('Command not accepted (auth level too low)')
		
		# if we reach here, we didn't have any use for this command
		# return False so the message will be tested against the response database
		return False
	
	def on_whoisaccount(self, bot, connection, event):
		self.callback_handler.update_parameters(
			'whois-' + event.arguments[0],
			{
				'auth_level': int(bot.db.get(
					'user|%s|%s' % (bot.server_name, event.arguments[1]),
					default_value = 0
				))
			}
		)
	
	def on_endofwhois(self, bot, connection, event):
		self.callback_handler.run('whois-' + event.arguments[0])
	
	def repeat_message_event(self, bot, connection, event, auth_level):
		# start over from scratch, so we can still continue to try to find a trigger match if auth is too low
		event_handler.fire('commands:on_message', (bot, connection, event, auth_level))
