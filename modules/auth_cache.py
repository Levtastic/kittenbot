def init():
	AuthCache()

class AuthCache():
	auth_cache = {}
	
	def __init__(self):
		event_handler.hook('commands:on_get_auth_level', self.on_get_auth_level)
		event_handler.hook('irc:on_whoisaccount', self.on_whoisaccount)
		
		event_handler.hook('irc:on_nick', self.on_nick)
		event_handler.hook('irc:on_kick', self.on_refresh)
		event_handler.hook('irc:on_part', self.on_refresh)
		event_handler.hook('irc:on_quit', self.on_refresh)
	
	def on_get_auth_level(self, bot, connection, event, nickname):
		if nickname in self.auth_cache:
			return self.auth_cache[nickname]
		
		return None
	
	def on_whoisaccount(self, bot, connection, event):
		nickname, account_name = event.arguments[0], event.arguments[1]
		
		if self.can_see(bot, nickname):
			self.auth_cache[nickname] = int(bot.db.get(
				'user|%s|%s' % (bot.server_name, account_name),
				default_value = 0
			))
	
	def on_nick(self, bot, connection, event):
		before = event.source.nick
		after = event.target

		if before in self.auth_cache:
			self.auth_cache[after] = self.auth_cache.pop(before)
	
	def on_refresh(self, bot, channel, event):
		if event.source.nick == channel.get_nickname():
			nicknames = self.auth_cache.keys()
		else:
			nicknames = [event.source.nick]
		
		for nickname in [n for n in nicknames if not self.can_see(bot, n)]:
			self.auth_cache.pop(nickname, True)
	
	def can_see(self, bot, nickname):
		visble_nicknames = []
		for channel in bot.channels.values():
			visble_nicknames += channel.users()
		
		return nickname in visble_nicknames
