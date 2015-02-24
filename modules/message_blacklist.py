import logging
import re

def init():
	MessageBlacklist()

class MessageBlacklist():
	def __init__(self):
		event_handler.hook('bot:on_before_send_message', self.on_before_send_message)
	
	def on_before_send_message(self, bot, connection, target, message, event):
		for blacklist in bot.db.get_all('message_blacklist'):
			if re.match(blacklist, message):
				message = 'Blacklist "%s" blocked message "%s" from being sent to %s' % (blacklist, message, target)
				
				logging.info(message)
				print(message)
				
				return False
		
		return True
