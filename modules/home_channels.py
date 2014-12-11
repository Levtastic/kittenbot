def init():
	HomeChannels()

class HomeChannels():
	def __init__(self):
		event_handler.hook('irc:on_welcome', self.on_welcome)
		event_handler.hook('irc:on_part', self.on_leave)
		event_handler.hook('irc:on_kick', self.on_leave)
	
	def on_welcome(self, bot, connection, event):
		for channel in self.homes():
			connection.join(channel)
	
	def on_leave(self, bot, connection, event):
		if event.source.nick == connection.get_nickname() and event.target in self.homes():
			connection.join(event.target)
	
	def homes(self):
		return bot.db.get_all('home|' + bot.server_name)
