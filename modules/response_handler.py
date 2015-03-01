import random
import re

def init():
	ResponseHandler()

class ResponseHandler():
	command_descriptions = {
		'codes': """
			Available codes: !server, !channel, !me, !speaker, !someone
			Use "help [!code]" for more information on a specific code
		""",
		'!server': """
			Replaced with the current server's name
			Example: -Where are we? = -We are in !channel, on !server
		""",
		'!channel': """
			Replaced with the channel the message is being sent to
			Example: -Where are we? = -We are in !channel
		""",
		'!me': """
			Replaced with the bot's current nickname
			Note: in triggers, this also matches any of the bot's aliases
			Example: -Hello !me = -Yes, I am !me, thank you for noticing
		""",
		'!speaker': """
			Replaced with whoever said the message that triggered a response.
			If the response wasn't triggered by a person, gets filled with a random person's name
			Example: -Hi bot = -Hello !speaker
		""",
		'!someone': """
			Replaced with a random nickname from the channel
			Note: Is never the bot's own name, and is only the same as !speaker if there is no one else in the channel for it to pick
			Example: -Who is cool? = -!someone is cool!
		""",
	}
	
	def __init__(self):
		event_handler.hook('help:get_command_description', self.get_command_description)
		
		# responses get checked last - only do this if no other module had a use for the message
		event_handler.hook('messages:on_handle_messages', self.on_handle_message, 1000)
		
		event_handler.hook('bot:on_process_message', self.on_process_message)
		
		# create regex patterns for case insensitive replacing
		self.speaker_pattern	= re.compile(re.escape('!speaker'),	re.IGNORECASE)
		self.channel_pattern	= re.compile(re.escape('!channel'),	re.IGNORECASE)
		self.someone_pattern	= re.compile(re.escape('!someone'),	re.IGNORECASE)
		self.me_pattern			= re.compile(re.escape('!me'),		re.IGNORECASE)
		self.server_pattern		= re.compile(re.escape('!server'),	re.IGNORECASE)
	
	def get_command_description(self, bot, command):
		if command in self.command_descriptions:
			return self.command_descriptions[command]
	
	def on_handle_message(self, bot, connection, event, message, is_public, is_action, reply_target, auth_level):
		message_type_code = is_action and '*' or '-'
		
		# Try to get a message as-is, then try swapping in aliases
		for name in [False, connection.get_nickname()] + bot.db.get_all('nick_alias'):
			if name:
				processed_message = re.sub(re.escape(name), '!me', message, flags = re.IGNORECASE)
			else:
				processed_message = message
			
			processed_message = bot.db.get_reply(processed_message, message_type_code, channel = reply_target)
			if processed_message:
				bot.send(connection, reply_target, processed_message, event)
				return True
		
		return False
	
	def on_process_message(self, bot, message, connection, event, channel):
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
		if channel in bot.channels:
			nicklist = [nick for nick in bot.channels[channel].users() if nick not in (me, speaker)]
			if nicklist:
				someone = random.choice(nicklist)
		
		# if we got a random name and we couldn't find a speaker before, re-set speaker to it
		if someone and speaker == me:
			speaker = someone
		
		# couldn't find anyone? make it the speaker
		# so if anyone uses it, it'll return the speaker's name
		# - incorrect, but not fatal
		if not someone:
			someone = speaker
		
		# apply regexes we compiled when the module was loaded
		message = self.speaker_pattern.sub(speaker, message)
		message = self.channel_pattern.sub(channel, message)
		message = self.someone_pattern.sub(someone, message)
		message = self.me_pattern.sub(me, message)
		message = self.server_pattern.sub(bot.server_name, message)
		
		return message
