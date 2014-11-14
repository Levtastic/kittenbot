import sys
import random
import irc.bot

from datetime import datetime

from callbackhandler import CallbackHandler
from responsedatabase import ResponseDatabase

class ResponseBot(irc.bot.SingleServerIRCBot):
	auth_commands = [
		'die',
		'add',
		'remove',
	]
	
	def __init__(self, nickname, realname, server, port = 6667, db_name = 'responsebot.db', command_aliases = {}, nick_aliases = [], random_timings = {}):
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
		self.command_aliases = command_aliases
		self.callback_handler = CallbackHandler()
		self.database = ResponseDatabase(db_name)
		self.nick_aliases = nick_aliases
		self.server_name = server
		self.random_timings = random_timings
		log('%s Initialised' % nickname)
	
	def on_nicknameinuse(self, connection, event):
		log('Unable to acquire nickname %s' % connection.get_nickname())
		self.die('')
	
	def on_welcome(self, connection, event):
		log('Connected as %s' % connection.get_nickname())
		if self.random_timings:
			connection.execute_every(1, self.random_actions_loop, (connection, ))
	
	def random_actions_loop(self, connection):
		for channel in self.channels:
			if random.randint(1, self.random_timings['part']) == 1:
				message = self.database.get_random('part_messages')
				if message:
					connection.action(channel, self.process_message(message, connection, channel = channel))
				connection.part(channel)
			
			elif random.randint(1, self.random_timings['action']) == 1:
				message = self.database.get_random('random_actions')
				if message:
					connection.action(channel, self.process_message(message, connection, channel = channel))
		
		for channel in self.database.get_channels(self.server_name):
			if channel not in self.channels and random.randint(1, self.random_timings['join']) == 1:
				connection.join(channel)
	
	def on_invite(self, connection, event):
		log('Invited to %s by %s' % (event.arguments[0], event.source.nick))
		connection.join(event.arguments[0])
	
	def on_join(self, connection, event):
		if event.source.nick == connection.get_nickname():
			log('Joined %s' % event.target)
			self.callback_handler.add(
				'greetchannel-%s' % event.target,
				self.greet_channel,
				{
					'channel': event.target,
					'connection': connection,
					'event': event,
				}
			)
	
	def on_part(self, connection, event):
		if event.source.nick == connection.get_nickname():
			log('Leaving %s' % event.target)
	
	def on_kick(self, connection, event):
		if event.arguments[0] == connection.get_nickname():
			log('Kicked from %s by %s for the following reason: %s' % (event.target, event.source.nick, event.arguments[1]))
	
	def on_namreply(self, connection, event):
		self.callback_handler.run('greetchannel-%s' % event.arguments[1])
	
	def greet_channel(self, channel, connection, event):
		message = self.database.get_random('join_messages')
		if message:
			connection.action(channel, self.process_message(message, connection, event))
	
	def on_privmsg(self, connection, event):
		self.do_command(connection, event, event.arguments[0])
	
	def on_action(self, connection, event):
		if event.target[0] != '#':
			return
		
		action = event.arguments[0].replace(connection.get_nickname(), '%(me)s')
		message = self.database.get_random_response(action)
		
		if message and len(self.nick_aliases) > 0:
			for alias in self.nick_aliases:
				action = action.replace(alias, '%(me)s')
			message = self.database.get_random_response(action)
		
		if message:
			if self.mentions_me(event.arguments[0], connection, event):
				message = self.database.get_random('random_mentions')
		
		if message:
			connection.action(event.target, self.process_message(message, connection, event))
	
	def on_pubmsg(self, connection, event):
		message_split = event.arguments[0].split(':', 1)
		if len(message_split) > 1 and message_split[0].lower().strip() == self.connection.get_nickname().lower():
			self.do_command(connection, event, message_split[1].strip().lower())
			return
		
		if self.mentions_me(event.arguments[0], connection, event):
			message = self.database.get_random('random_mentions')
			if message:
				connection.action(event.target, self.process_message(message, connection, event))
	
	def on_whoisuser(self, connection, event):
		if len(event.arguments) < 4:
			auth_level = 0
		else:
			auth_level = self.database.get_whois_auth_level(event.arguments[4])
		
		self.callback_handler.run('whois-%s' % event.arguments[0], {'auth_level': auth_level})
	
	def do_command(self, connection, event, command, auth_level = None):
		parameters = ''
		command_split = command.split(' ', 1)
		if len(command_split) == 2:
			command, parameters = command_split
		
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
			
			if command == 'die' and auth_level >= 80:
				log('"%s" command issued by %s in %s' % (command, event.source.nick, event.target))
				self.quit(connection, event)
		
		message = self.database.get_random('unknown_command_messages')
		if message:
			connection.action(event.target, self.process_message(message, connection, event))
	
	def process_message(self, message, connection, event = None, channel = None):
		me = connection.get_nickname()
		someone = ''
		if event:
			speaker = event.source.nick
			channel = event.target 
		else:
			speaker = me
		
		if channel in self.channels:
			nicklist = [nick for nick in self.channels[channel].users()
				if nick not in (me, speaker)]
			if nicklist:
				someone = random.choice(nicklist)
		
		if not someone:
			someone = speaker
		
		return message % {
			'speaker': speaker,
			'channel': channel,
			'me': me,
			'someone': someone,
		}
	
	def mentions_me(self, message, connection, event):
		message = message.lower()
		return connection.get_nickname().lower() in message or any(name.lower() in message for name in self.nick_aliases)
	
	def quit(self, connection, event):
		for channel in self.channels:
			message = self.database.get_random('part_messages')
			if message:
				connection.action(channel, self.process_message(message, connection, event))
			connection.part(channel)
		self.die('')

def log(message):
	print('[%s] %s' % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message))