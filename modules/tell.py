from datetime import datetime, timedelta
from collections import defaultdict

def init():
	Tell()

class Tell():
	auth_commands = {
		'tell': 0,
	}
	command_descriptions = {
		'tell': """
			Stores a message to be sent later when someone is around
			[message] will be sent to [nick] whenever they next speak in the channel the command was issued in
			Syntax: tell [nick] [message]
		""",
	}
	
	def __init__(self):
		event_handler.hook('modulehandler:before_init_modules', self.on_before_init_modules)
		event_handler.hook('modulehandler:after_load_modules', self.on_after_load_modules)
		
		event_handler.hook('help:get_command_description', self.get_command_description)
		
		event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
		event_handler.hook('commands:do_auth_command', self.do_auth_command)
		
		event_handler.hook('messages:on_handle_messages', self.on_handle_messages)
		
		self.messages = defaultdict(lambda: defaultdict(list))
	
	def on_before_init_modules(self, module_handler, bot, event_handler, first_time):
		bot.module_parameters['tell:messages'] = self.messages
	
	def on_after_load_modules(self, module_handler, bot, event_handler, first_time):
		self.messages = bot.module_parameters.pop('tell:messages', self.messages)
	
	def get_command_description(self, bot, command):
		if command in self.command_descriptions:
			return self.command_descriptions[command]
	
	def get_auth_commands(self, bot):
		return self.auth_commands
	
	def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
		if command not in self.auth_commands:
			return False # not for us
		
		if not parameters:
			return False
		
		if command == 'tell':
			try:
				nick, message = parameters.strip().split(' ', 1)
			except ValueError:
				return False
			
			self.messages[reply_target][nick.lower()].append(
				StoredMessage(nick, event.source, message.strip())
			)
			bot.send(connection, reply_target, bot.db.get_random('yes'), event)
			return True
		
		return False
	
	def on_handle_messages(self, bot, connection, event, message, is_public, is_action, reply_target, auth_level):
		if not is_public:
			return False
		
		speaker_key = event.source.nick.lower()
		
		if not self.messages[reply_target][speaker_key]:
			return False
		
		for stored_message in self.messages[reply_target][speaker_key]:
			time_delta = datetime.now() - stored_message.datetime
			
			days = time_delta.days
			if days:
				time_delta -= timedelta(days = days)
			
			hours, remainder = divmod(time_delta.seconds, 3600)
			minutes, seconds = divmod(remainder, 60)
			
			time_pieces = []
			days and time_pieces.append(self.format_time_piece('day', days))
			hours and time_pieces.append(self.format_time_piece('hour', hours))
			minutes and time_pieces.append(self.format_time_piece('minute', minutes))
			seconds and time_pieces.append(self.format_time_piece('second', seconds))
			
			message = '%s: message from %s %s: %s' % (
				event.source.nick,
				stored_message.source.nick,
				time_pieces and ', '.join(time_pieces) + ' ago' or 'just now',
				stored_message.message,
			)
			
			bot.send(connection, reply_target, message, event, process_message = False)
		
		self.messages[reply_target][speaker_key].clear()
		
		return False
	
	def format_time_piece(self, name, value):
		return '%d %s%s' % (value, name, value > 1 and 's' or '')

class StoredMessage():
	def __init__(self, destination, source, message):
		self.destination = destination
		self.source = source
		self.message = message
		
		self.datetime = datetime.now()
