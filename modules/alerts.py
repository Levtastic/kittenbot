import logging

from callbackhandler import CallbackHandler

def init():
	Alerts()

class Alerts():
	def __init__(self):
		event_handler.hook('undo:on_undo', self.on_undo)
		event_handler.hook('undo:on_redo', self.on_redo)
		
		event_handler.hook('db_commands:on_after_add', self.on_after_add)
		event_handler.hook('db_commands:on_before_remove', self.on_before_remove)
		event_handler.hook('db_commands:on_after_remove', self.on_after_remove)
		event_handler.hook('db_commands:on_before_set', self.on_before_set)
		event_handler.hook('db_commands:on_after_set', self.on_after_set)
		
		self.callback_handler = CallbackHandler()
	
	def on_undo(self, bot, connection, event, command, parameters, reply_target, auth_level):
		message = 'Undid last for %s in %s' % (event.source.nick, event.target)
		
		logging.info(message)
		
		for contact in bot.db.get_all('alert_contact'):
			bot.send(connection, contact, '-' + message, event)
	
	def on_redo(self, bot, connection, event, command, parameters, reply_target, auth_level):
		message = 'Redid last for %s in %s' % (event.source.nick, event.target)
		
		logging.info(message)
		
		for contact in bot.db.get_all('alert_contact'):
			bot.send(connection, contact, '-' + message, event)
	
	def on_after_add(self, bot, connection, event, reply_target, auth_level, key, value):
		message = 'Learned "%s = %s" from %s in %s' % (key, value, event.source.nick, event.target)
		
		logging.info(message)
		
		for contact in bot.db.get_all('alert_contact'):
			bot.send(connection, contact, '-' + message, event)
	
	def on_before_remove(self, bot, connection, event, reply_target, auth_level, key, value):
		db_key, old_value = bot.db.get_key_value(key, value)
		if db_key and old_value:
			self.callback_handler.add(
				'remove|%s|%s' % (key, value),
				self.send_remove_message,
				(bot, connection, event, db_key, old_value)
			)
	
	def on_after_remove(self, bot, connection, event, reply_target, auth_level, key, value):
		self.callback_handler.run('remove|%s|%s' % (key, value))
	
	def on_before_set(self, bot, connection, event, reply_target, auth_level, key, values):
		old_values = bot.db.get_all(key)
		if old_values:
			self.callback_handler.add(
				'set|%s|%s' % (key, '|'.join(values)),
				self.send_set_message,
				(bot, connection, event, key, old_values, values)
			)
	
	def on_after_set(self, bot, connection, event, reply_target, auth_level, key, values):
		self.callback_handler.run('set|%s|%s' % (key, '|'.join(values)))
	
	def send_remove_message(self, bot, connection, event, key, old_value):
		message = 'Forgot "%s = %s" for %s in %s' % (key, old_value, event.source.nick, event.target)
		
		logging.info(message)
		
		for contact in bot.db.get_all('alert_contact'):
			bot.send(connection, contact, '-' + message, event)
	
	def send_set_message(self, bot, connection, event, key, old_values, new_values):
		message = '%s set from "%s" to "%s" by %s in %s' % (key, ', '.join(old_values), ', '.join(new_values), event.source.nick, event.target)
		
		logging.info(message)
		
		for contact in bot.db.get_all('alert_contact'):
			bot.send(connection, contact, '-' + message, event)
