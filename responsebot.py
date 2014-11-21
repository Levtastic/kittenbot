import sys
import re
import random
import logging
import irc.bot

from callbackhandler import CallbackHandler
from responsedatabase import ResponseDatabase
from helphandler import HelpHandler

class ResponseBot(irc.bot.SingleServerIRCBot):
	auth_commands = {
		'help': 30,
		'add': 30, # only exception is adding channels, which is hard-coded at 50 (needs better solution)
		'list': 30,
		'remove': 30,
		'send': 60,
		'say': 60,
		'do': 60,
		'join': 60,
		'part': 60,
		'blacklist': 60,
		'unblacklist': 60,
		'die': 80,
		'sql': 90,
	}
	table_aliases = {
		'complete': 'completed_command_messages',
		'unknown': 'unknown_command_messages',
		'mention': 'random_mentions',
		'random': 'random_messages',
		'trigger': 'response_messages',
		'join': 'join_messages',
		'part': 'part_messages',
		'channel': 'channels',
		'user': 'users',
	}
	talked_last = []
	
	def __init__(self, nickname, realname, server, port = 6667, db_name = 'responsebot.db', join_commands = [], command_aliases = {}, nick_aliases = [], random_timings = {}):
		# init bot framework
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
		
		# max of 2 messages a second, to avoid flooding out
		# note: may cause blocking which could make the bot fail to respond to a ping
		self.connection.set_rate_limit(2)
		
		# add built in command aliases
		command_aliases.update({
			'act': 'do',
			'leave': 'part',
			'forget': 'remove',
			'delete': 'remove',
			'remember': 'add',
		})
		
		# store passed variables for later use
		self.join_commands = join_commands
		self.command_aliases = command_aliases
		self.nick_aliases = nick_aliases
		self.server_name = server
		self.random_timings = random_timings
		
		# set up helper classes for later use
		self.callback_handler = CallbackHandler()
		self.database = ResponseDatabase(db_name)
		self.help_handler = HelpHandler(self.auth_commands, self.command_aliases, self.table_aliases)
		
		# create regex patterns for case insensitive replacing
		self.replace_patterns = {
			'speaker': re.compile(re.escape('!speaker'), re.IGNORECASE),
			'channel': re.compile(re.escape('!channel'), re.IGNORECASE),
			'someone': re.compile(re.escape('!someone'), re.IGNORECASE),
			'me': re.compile(re.escape('!me'), re.IGNORECASE),
		}
		
		# and we're done!
		logging.info('%s Initialised' % nickname)
	
	def on_nicknameinuse(self, connection, event):
		# someone using our nickname? abort - bot may already be running on this server
		logging.error('Unable to acquire nickname %s' % connection.get_nickname())
		self.die('')
	
	def on_welcome(self, connection, event):
		logging.info('Connected as %s' % connection.get_nickname())
		
		for join_command in self.join_commands:
			func_name, params = join_command
			func = getattr(connection, func_name)
			if func:
				func(**params)
		
		# random messages loop only started if the bot is set up with random timings
		if self.random_timings:
			connection.execute_every(1, self.random_messages_loop, (connection, ))
	
	def random_messages_loop(self, connection):
		if not connection.is_connected():
			return
		
		for channel in self.channels:
			# only message / part if we weren't the last person to talk in this channel
			if not channel in self.talked_last:
				if random.randint(1, self.random_timings['part']) == 1:
					self.send(connection, channel, self.database.get_random('part_messages'))
					connection.part(channel)
				
				elif random.randint(1, self.random_timings['message']) == 1:
					self.send(connection, channel, self.database.get_random('random_messages'))
		
		# every channel we know about, but aren't in
		for channel in self.database.get_channels(self.server_name):
			if channel not in self.channels and random.randint(1, self.random_timings['join']) == 1:
				connection.join(channel)
	
	def on_privnotice(self, connection, event):
		if event.source and event.source.nick != 'Global':
			logging.info('Private notice from %s: "%s"' % (event.source.nick, event.arguments[0]))
	
	def on_invite(self, connection, event):
		# invites can only be sent by channel ops, so we don't need to worry too much about this being abused
		logging.info('Invited to %s by %s' % (event.arguments[0], event.source.nick))
		connection.join(event.arguments[0].lower())
	
	def on_join(self, connection, event):
		if event.source.nick == connection.get_nickname():
			logging.info('Joined %s' % event.target)
			# register a callback for when we get the namreply for this channel, and know who's in it
			# (necessary for use of !someone in greeting messages)
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
			if event.target in self.talked_last:
				self.talked_last.remove(event.target)
			
			logging.info('Leaving %s' % event.target)
	
	def on_kick(self, connection, event):
		if event.arguments[0] == connection.get_nickname():
			if event.target in self.talked_last:
				self.talked_last.remove(event.target)
			
			logging.info('Kicked from %s by %s for the following reason: %s' % (event.target, event.source.nick, event.arguments[1]))
			
			# add channel to blacklist until an admin re-allows it, in case the bot was kicked for misbehaving
			self.database.set_channel_blacklist(event.target, self.server_name, True, 'Kicked by %s for the following reason: %s' % (event.source.nick, event.arguments[1]))
	
	def on_namreply(self, connection, event):
		# we just got the information that populates the channel user list? now we can greet the channel
		self.callback_handler.run('greetchannel-%s' % event.arguments[1])
	
	def greet_channel(self, channel, connection, event):
		message = self.database.get_random('join_messages')
		if message:
			self.send(connection, channel, message, event)
	
	def on_privmsg(self, connection, event):
		self.on_message(connection, event, is_action = False, is_public = False)
	
	def on_pubmsg(self, connection, event):
		self.on_message(connection, event, is_action = False, is_public = True)
	
	def on_action(self, connection, event):
		self.on_message(connection, event, is_action = True, is_public = event.target[0] == '#')
	
	def on_message(self, connection, event, is_action = False, is_public = True):
		reply_target = is_public and event.target or event.source.nick
		
		# we just got a message! We're no longer the last person to talk here
		if reply_target in self.talked_last:
			self.talked_last.remove(reply_target)
		
		# Try to get a message with just our name replaced
		trigger = event.arguments[0].replace(connection.get_nickname(), '!me')
		if self.send(connection, reply_target, self.database.get_random_response(trigger, is_action), event):
			return
		
		# if we didn't get one, try again with all our aliases replaced
		if self.nick_aliases:
			for alias in self.nick_aliases:
				trigger = trigger.replace(alias, '!me')
			if self.send(connection, reply_target, self.database.get_random_response(trigger, is_action), event):
				return
		
		# still no message? check if it's a command
		if not is_action:
			if not is_public:
				# if sent in private, try it as a command
				self.do_command(connection, event, event.arguments[0], reply_target)
				return
			
			# if prefixed by our name, try it as a command
			message_split = event.arguments[0].split(':', 1)
			if len(message_split) == 2 and message_split[0].lower().strip() == self.connection.get_nickname().lower():
				self.do_command(connection, event, message_split[1], reply_target)
				return
		
		# not a command? check if it mentions us and send a random reply
		if self.mentions_me(event.arguments[0], connection, event):
			if self.send(connection, reply_target, self.database.get_random('random_mentions'), event):
				return
		
		# still no hit? Nothing to do with us, move along.
	
	def send(self, connection, target, message, event = None):
		if not message:
			return False
		
		if target[0] == '#' and target not in self.channels:
			return False
		
		message_text, message_type = message
		send_method = message_type == 'action' and connection.action or connection.privmsg
		
		send_method(target, self.process_message(message_text, connection, event, target))
		
		# we just talked in this channel - we don't want to be the next to talk (responsebots are shy) so we record this for later
		self.talked_last.append(target)
		
		return True
	
	def do_command(self, connection, event, full_command, reply_target, auth_level = None):
		try:
			command, parameters = full_command.strip().split(' ', 1)
		except ValueError:
			command = full_command
			parameters = ''
		
		command = command.strip().lower()
		
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
						'full_command': full_command,
						'reply_target': reply_target,
					}
				)
				connection.whois(event.source.nick)
				return # we'll come back when we have more information
			
			logging.info('"%s" command issued by %s (auth level %d) in %s' % (full_command, event.source.nick, auth_level, event.target))
			
			if auth_level >= self.auth_commands[command]:
				if command == 'die': # ResponseBot: die
					self.send(connection, reply_target, self.database.get_random('completed_command_messages'), event)
					self.quit(connection, event, parameters)
					return
				
				elif command == 'send': # ResponseBot: send message #responsebot Hello world!
					try:
						message_type, channel, message_text = parameters.strip().split(' ', 2)
					except ValueError:
						pass
					else:
						if channel[0] != '#' or channel.lower() in self.channels:
							self.send(connection, reply_target, self.database.get_random('completed_command_messages'), event)
							self.send(connection, channel.lower(), (message_text.strip(), message_type.lower()), event)
							return
				
				elif command == 'say': # ResponseBot: say #responsebot Hello World!
					try:
						channel, message_text = parameters.strip().split(' ', 1)
					except ValueError:
						pass
					else:
						if channel[0] != '#' or channel.lower() in self.channels:
							self.send(connection, reply_target, self.database.get_random('completed_command_messages'), event)
							self.send(connection, channel.lower(), (message_text.strip(), 'message'), event)
							return
				
				elif command == 'do': # ResponseBot: do #responsebot dances!
					try:
						channel, message_text = parameters.strip().split(' ', 1)
					except ValueError:
						pass
					else:
						if channel[0] != '#' or channel.lower() in self.channels:
							self.send(connection, reply_target, self.database.get_random('completed_command_messages'), event)
							self.send(connection, channel.lower(), (message_text.strip(), 'action'), event)
							return
				
				elif command == 'join': # ResponseBot: join #responsebot
					if parameters and parameters[0] == '#':
						connection.join(parameters.strip().lower())
						self.send(connection, reply_target, self.database.get_random('completed_command_messages'), event)
						return
				
				elif command == 'part': # ResponseBot: part #responsebot
					params = parameters.strip().split(' ', 1)
					
					if len(params) == 2:
						channel = params[0]
						message = params[1]
					else:
						channel = params[0]
						message = ''
					
					if channel:
						if channel[0] != '#':
							channel = '#' + channel
						
						if channel in self.channels:
							self.send(connection, channel, self.database.get_random('part_messages'), event)
							connection.part(channel, message.strip())
							if reply_target.lower() == parameters.lower():
								reply_target = event.source.nick
							self.send(connection, reply_target, self.database.get_random('completed_command_messages'), event)
							return
				
				elif command == 'sql': # ResponseBot: sql force SELECT * FROM users
					try:
						force, command = parameters.strip().split(' ', 1)
					except ValueError:
						pass
					else:
						if force == 'force' and self.database.do_sql(connection, reply_target, command):
							self.send(connection, reply_target, self.database.get_random('completed_command_messages'), event)
							return
				
				elif command == 'blacklist':
					params = parameters.strip().split(' ', 1)
					if len(params) == 2:
						channel = params[0]
						reason = params[1]
					else:
						channel = params[0]
						reason = ''
					
					if channel[0] != '#':
						channel = '#' + channel
					
					self.database.set_channel_blacklist(channel, self.server_name, True, reason)
					self.send(connection, reply_target, self.database.get_random('completed_command_messages'), event)
					return
				
				elif command == 'unblacklist':
					params = parameters.strip().split(' ', 1)
					if len(params) == 2:
						channel = params[0]
						reason = params[1]
					else:
						channel = params[0]
						reason = ''
					
					if channel[0] != '#':
						channel = '#' + channel
					
					self.database.set_channel_blacklist(channel, self.server_name, False, reason)
					self.send(connection, reply_target, self.database.get_random('completed_command_messages'), event)
					return
					
				# ResponseBot: help add trigger
				elif command == 'help' and self.help_handler.do_command(connection, event.source.nick, parameters, auth_level):
					return
				
				# ResponseBot: add trigger action pokes ResponseBot = action bites !speaker
				# ResponseBot: remove trigger 6
				# ResponseBot: list trigger 2 pokes
				elif self.database.do_command(connection, self.server_name, reply_target, self.table_aliases, command, parameters, auth_level, [connection.get_nickname()] + self.nick_aliases):
					self.send(connection, reply_target, self.database.get_random('completed_command_messages'), event)
					return
			
			else:
				logging.info('Command not accepted (auth level too low)')
		
		self.send(connection, reply_target, self.database.get_random('unknown_command_messages'), event)
	
	def on_whoisuser(self, connection, event):
		# check we can see an account name - if not, we give them an auth level of 0
		if len(event.arguments) < 4:
			auth_level = 0
		else:
			auth_level = self.database.get_whois_auth_level(event.arguments[4], self.server_name)
		
		self.callback_handler.run('whois-%s' % event.arguments[0], {'auth_level': auth_level})
	
	def process_message(self, message, connection, event = None, channel = None):
		me = connection.get_nickname()
		someone = ''
		
		# get channel from event if possible, otherwise use passed variables
		if event:
			speaker = event.source.nick
			channel = event.target 
		else:
			# in this context there is no speaker,
			# so if anyone uses it, it'll return the current bot name
			# - incorrect, but not fatal
			speaker = me
		
		# !someone can be anyone except kitten and the speaker (ideally)
		if channel in self.channels:
			nicklist = [nick for nick in self.channels[channel].users()
				if nick not in (me, speaker)]
			if nicklist:
				someone = random.choice(nicklist)
		
		# couldn't find anyone? make it the speaker
		# so if anyone uses it, it'll return the speaker's name
		# - incorrect, but not fatal
		if not someone:
			someone = speaker
		
		message = self.replace_patterns['speaker'].sub(speaker, message)
		message = self.replace_patterns['channel'].sub(channel, message)
		message = self.replace_patterns['me'].sub(me, message)
		message = self.replace_patterns['someone'].sub(someone, message)
		
		return message
	
	def mentions_me(self, message, connection, event):
		return any(name.lower() in message.lower() for name in [connection.get_nickname()] + self.nick_aliases)
	
	def quit(self, connection, event, message = ''):
		for channel in self.channels:
			# say goodbye!
			self.send(connection, channel, self.database.get_random('part_messages'), event)
			connection.part(channel, message)
		self.die(message)
