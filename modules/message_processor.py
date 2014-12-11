import random
import re

def init():
	MessageProcessor()

class MessageProcessor():
	def __init__(self):
		event_handler.hook('bot:on_get_message_processor', self.on_get_message_processor)
		
		# create regex patterns for case insensitive replacing
		self.speaker_pattern	= re.compile(re.escape('!speaker'),	re.IGNORECASE)
		self.channel_pattern	= re.compile(re.escape('!channel'),	re.IGNORECASE)
		self.someone_pattern	= re.compile(re.escape('!someone'),	re.IGNORECASE)
		self.me_pattern			= re.compile(re.escape('!me'),		re.IGNORECASE)
		self.server_pattern		= re.compile(re.escape('!server'),	re.IGNORECASE)
	
	def on_get_message_processor(self, bot, message, connection, event, channel):
		return self.process_message
	
	def process_message(self, bot, message, connection, event, channel):
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
