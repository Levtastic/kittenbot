import logging

def init():
	ChannelCommands()

class ChannelCommands():
	auth_commands = {
		'join': 60,
		'part': 60,
		'blacklist': 60,
		'unblacklist': 60,
	}
	command_descriptions = {
		'join': """
			Joins the given channel
			Syntax: join [#channel]
		""",
		'part': """
			Leaves the given channel
			Syntax: part [#channel] [part message]
		""",
		'blacklist': """
			Blacklists a channel
			Blacklisted channels will not be automatically joined by the bot's random event loop
			Syntax: blacklist [#channel] [reason]
		""",
		'unblacklist': """
			Unblacklists a blacklisted channel
			Blacklisted channels will not be automatically joined by the bot's random event loop
			Syntax: unblacklist [#channel]
		""",
	}
	
	def __init__(self):
		event_handler.hook('help:get_command_description', self.get_command_description)
		
		event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
		event_handler.hook('commands:do_auth_command', self.do_auth_command)
	
	def get_command_description(self, bot, command):
		if command in self.command_descriptions:
			return self.command_descriptions[command]

	def get_auth_commands(self, bot):
		return self.auth_commands

	def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
		if command not in self.auth_commands:
			return False # not for us
		
		if command == 'join': # ResponseBot: join #responsebot
			if parameters and parameters[0] == '#':
				connection.join(parameters.strip().lower())
				bot.send(connection, reply_target, bot.db.get_random('yes'), event)
				return True
		
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
				
				if channel in bot.channels:
					# send the confirmation first in case we're about to leave reply_target
					bot.send(connection, reply_target, bot.db.get_random('yes'), event)
					
					bot.send(connection, channel, bot.db.get_random('part'), event)
					connection.part(channel, message.strip())
					
					return True
		
		elif command in ('blacklist', 'unblacklist'):
			parameters = parameters.strip().split(' ', 1)
				
			if len(parameters) == 2:
				channel = parameters[0]
				reason = parameters[1]
			else:
				channel = parameters[0]
				reason = ''
			
			if channel[0] != '#':
				channel = '#' + channel
			
			if command == 'blacklist':
				success = self.blacklist(bot, channel, reason)
			else:
				success = self.unblacklist(bot, channel)
			
			if success:
				bot.send(connection, reply_target, bot.db.get_random('yes'), event)
				return True
		
		return False
	
	def blacklist(self, bot, channel, reason):
		if not bot.db.delete('channel|' + bot.server_name, channel):
			return False
		
		bot.db.add('channel|%s|blacklisted' % bot.server_name, '%s|%s' % (channel, reason))
		
		return True
	
	def unblacklist(self, bot, channel):
		if not bot.db.delete('channel|%s|blacklisted' % bot.server_name, channel + '%'):
			return False
		
		bot.db.add('channel|' + bot.server_name, channel)
		
		return True
