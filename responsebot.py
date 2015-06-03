import logging
import irc.bot

from modulehandler import ModuleHandler

class ResponseBot(irc.bot.SingleServerIRCBot):
	def __init__(self, nickname, realname, server_name, server, port = 6667, module_parameters = {}):
		# init bot framework
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
		
		# set lenient encoding to avoid encoding-related crash
		irc.client.ServerConnection.buffer_class = irc.buffer.LenientDecodingLineBuffer
		
		# store passed variables for later use
		self.server_name = server_name
		self.module_parameters = module_parameters
		
		# set up helper classes for later use
		self.module_handler = ModuleHandler(self)
		
		# max messages a second, to avoid flooding out
		# note: may cause blocking which could make the bot fail to respond to a ping
		rate_limit = float(self.db.get('connection_rate_limit', default_value = 0))
		if rate_limit:
			self.connection.set_rate_limit(rate_limit)
		
		# hook into IRC event handler to pass events to our event handler
		self.reactor.add_global_handler('all_events', self._irc_events)
		
		# init event
		self.module_handler.fire_event('bot:finish_init', self)
	
	def _irc_events(self, connection, event):
		self.module_handler.fire_event('irc:on_' + event.type, (self, connection, event))
	
	def start(self):
		self.module_handler.fire_event('bot:on_start', self)
		super(ResponseBot, self).start()
	
	def send(self, connection, target, message, event = None, process_message = True):
		if any(result is False for result in self.module_handler.fire_event('bot:on_before_send_message', (self, connection, target, message, event))):
			return False
		
		if process_message:
			for process_function in self.module_handler.get_event_handlers('bot:on_process_message'):
				try:
					message = process_function(self, message, connection, event, target)
				except BaseException as e:
					error = 'error in message processing function: %s: %s' % (type(e).__name__, e)
					logging.exception(error)
					print(error)
		
		if not message or not isinstance(message, str):
			return False
		
		sent_by_module = True
		if not any(result is True for result in self.module_handler.fire_event('bot:on_send_message', (self, connection, target, message, event, process_message))):
			try:
				# default behaviour, if nothing has overridden it
				connection.privmsg(target, message)
				sent_by_module = False
			except BaseException as e:
				error = 'unable to send "%s" to %s: %s: %s' % (message, target, type(e).__name__, e)
				logging.exception(error)
				print(error)
				return False
		
		self.module_handler.fire_event('bot:on_after_send_message', (self, connection, target, message, event, sent_by_module))
		
		return True
	
	def quit(self, connection, event, message = ''):
		for process_function in self.module_handler.get_event_handlers('bot:on_quit'):
			try:
				if process_function(self, connection, event, message) is False:
					return False
			except BaseException as e:
				error = 'error in message processing function: %s: %s' % (type(e).__name__, e)
				logging.exception(error)
				print(error)
		
		# die later, after any final issues have been handled
		connection.execute_delayed(1, self.die, (message, ))
		return True
