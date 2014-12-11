import logging
import irc.bot

from modulehandler import ModuleHandler

class ResponseBot(irc.bot.SingleServerIRCBot):
	def __init__(self, nickname, realname, server_name, server, port = 6667, module_parameters = {}):
		# init bot framework
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
		
		# max of 2 messages a second, to avoid flooding out
		# note: may cause blocking which could make the bot fail to respond to a ping
		self.connection.set_rate_limit(2)
		
		# store passed variables for later use
		self.server_name = server_name
		self.module_parameters = module_parameters
		
		# set up helper classes for later use
		self.module_handler = ModuleHandler(self)
		
		# hook into IRC event handler to pass events to our event handler
		self.manifold.add_global_handler("all_events", self.irc_events)
		
		# init event
		self.module_handler.fire_event('bot:finish_init', self)
	
	def irc_events(self, connection, event):
		self.module_handler.fire_event('irc:on_' + event.type, (self, connection, event))
	
	def start(self):
		self.module_handler.fire_event('bot:on_start', self)
		super(ResponseBot, self).start()
	
	def send(self, connection, target, message, event = None):
		if any(result is False for result in self.module_handler.fire_event('bot:on_before_send_message', (self, connection, target, message, event))):
			return False
		
		message = self.process_message(message, connection, event, target)
		
		if not message or not isinstance(message, str):
			return False
		
		sent_by_module = True
		if not any(result is True for result in self.module_handler.fire_event('bot:send_message', (self, connection, target, message, event))):
			try:
				connection.privmsg(target, message) # default behaviour, if nothing has overridden it
				sent_by_module = False
			except BaseException as e:
				error = 'unable to send "%s" to %s: %s %s' % (message, target, str(type(e)), e)
				logging.error(error)
				print(error)
				return False
		
		self.module_handler.fire_event('bot:on_after_send_message', (self, connection, target, message, event, sent_by_module))
		
		return True
	
	def process_message(self, message, connection, event = None, channel = None):
		results = self.module_handler.fire_event('bot:on_get_message_processor', (self, message, connection, event, channel))
		
		for process_function in [function for function in results if callable(function)]:
			try:
				message = process_function(self, message, connection, event, channel)
			except BaseException as e:
				error = 'error in message processing function: %s %s' % (str(type(e)), e)
				logging.exception(error)
				print(error)
		
		return message
	
	def quit(self, connection, event, message = ''):
		if any(result is False for result in self.module_handler.fire_event('bot:on_quit', (self, connection, event, message))):
			return False
		
		connection.execute_delayed(1, self.die, (message, ))
		return True
