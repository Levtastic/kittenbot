import sys
import random
import irc.bot

from datetime import datetime

from callbackhandler import CallbackHandler
from responsedatabase import ResponseDatabase

class ResponseBot(irc.bot.SingleServerIRCBot):
	auth_commands = [
		'die',
	]
	
	def __init__(self, nickname, realname, server, port = 6667, db_name = 'responsebot.db', command_aliases = {}, nick_aliases = []):
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
		self.command_aliases = command_aliases
		self.callback_handler = CallbackHandler()
		self.database = ResponseDatabase(db_name)
		self.channel_list = self.database.get_channels(self.server_list[0].host)
		self.nick_aliases = nick_aliases
		log('%s Initialised' % nickname)
	
	def on_nicknameinuse(self, connection, event):
		log('Unable to acquire nickname %s' % connection.get_nickname())
		self.die()
	
	def on_welcome(self, connection, event):
		log('Connected as %s' % connection.get_nickname())
		for channel in self.channel_list:
			connection.join(channel)
	
	def on_join(self, connection, event):
		if event.source.nick == connection.get_nickname():
			self.callback_handler.add(
				'greetchannel-%s' % event.target,
				self.greet_channel,
				{
					'channel': event.target,
					'connection': connection,
					'event': event,
				}
			)
	
	def on_namreply(self, connection, event):
		self.callback_handler.run('greetchannel-%s' % event.arguments[1])
	
	def greet_channel(self, channel, connection, event):
		message = self.database.get_random('join_messages')
		if len(message) > 0:
			connection.action(channel, self.process_message(message, connection, event))
	
	def on_privmsg(self, connection, event):
		self.do_command(connection, event, event.arguments[0])
	
	def on_action(self, connection, event):
		if event.target[0] != '#':
			return
		
		message = self.database.get_random_response(event.arguments[0].replace(connection.get_nickname(), '%(me)s'))
		if len(message) == 0:
			if self.mentions_me(event.arguments[0], connection, event):
				message = self.database.get_random('random_mentions')
		
		if len(message) > 0:
			connection.action(event.target, self.process_message(message, connection, event))
	
	def on_pubmsg(self, connection, event):
		messagesplit = event.arguments[0].split(':', 1)
		if len(messagesplit) > 1 and messagesplit[0].lower().strip() == self.connection.get_nickname().lower():
			self.do_command(connection, event, messagesplit[1].strip().lower())
			return
		
		if self.mentions_me(event.arguments[0], connection, event):
			message = self.database.get_random('random_mentions')
			if len(message) > 0:
				connection.action(event.target, self.process_message(message, connection, event))
	
	def on_whoisuser(self, connection, event):
		if len(event.arguments) < 4:
			auth_level = 0
		else:
			auth_level = self.database.get_whois_auth_level(event.arguments[4])
		
		self.callback_handler.run('whois-%s' % event.arguments[0], {'auth_level': auth_level})
	
	def do_command(self, connection, event, command, auth_level = None):
		if command in self.command_aliases:
			command = self.command_aliases[command]
		
		if command in self.auth_commands:
			if auth_level is None:
				self.callback_handler.add(
					'whois-%s' % event.source.nick,
					self.do_command,
					{
						'connection': connection,
						'event': event,
						'command': command,
					}
				)
				connection.whois(event.source.nick)
				return # we'll do this later when we have more information
			
			log('"%s" command issued by %s in %s' % (command, event.source.nick, event.target))
			
			if command == 'die' and auth_level >= 80:
				self.quit(connection, event)
				return
		
		message = self.database.get_random('unknown_command_messages')
		if len(message) > 0:
			connection.action(event.target, self.process_message(message, connection, event))
	
	def process_message(self, message, connection, event):
		someone = ''
		me = connection.get_nickname()
		if event.target in self.channels:
			nicklist = list(self.channels[event.target].users())
			if len(nicklist) > 2:
				nicklist.remove(me)
				if event.source.nick in nicklist:
					nicklist.remove(event.source.nick)
				someone = random.choice(nicklist)
		
		if len(someone) == 0:
			someone = event.source.nick
		
		return  message % {
			'speaker': event.source.nick,
			'channel': event.target,
			'me': me,
			'someone': someone,
		}
	
	def mentions_me(self, message, connection, event):
		message = message.lower()
		return connection.get_nickname().lower() in message or any(name.lower() in message for name in self.nick_aliases)
	
	def quit(self, connection, event):
		for channel in self.channel_list:
			message = self.database.get_random('part_messages')
			if len(message) > 0:
				connection.action(channel, self.process_message(message, connection, event))
			connection.part(channel)
		self.die('zzz')

def log(message):
	print('[%s] %s' % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message))