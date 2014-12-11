def init():
	Nickname()

class Nickname():
	nick_delay = 60 * 5
	
	def __init__(self):
		event_handler.hook('irc:on_welcome', self.on_welcome)
		event_handler.hook('irc:on_nick', self.on_nick)
		event_handler.hook('irc:on_nicknameinuse', self.on_nicknameinuse)
		event_handler.hook('irc:on_nickcollision', self.on_nicknameinuse)
		event_handler.hook('irc:on_unavailresource', self.on_nicknameinuse)
		event_handler.hook('irc:on_nonicknamegiven', self.on_nonicknamegiven)
	
	def on_welcome(self, bot, connection, event):
		nicklist = self.names()
		if connection.get_nickname() in nicklist and connection.get_nickname() != nicklist[0]:
			connection.nick(nicklist[0])
	
	def on_nick(self, bot, connection, event):
		if event.target == connection.get_nickname():
			nicklist = self.names()
			if event.target not in nicklist:
				return # must have been manually renicked
			
			if nicklist.index(event.target) != 0:
				connection.execute_delayed(self.nick_delay, self.get_ideal_nick, (bot, connection))
	
	def get_ideal_nick(self, bot, connection):
		nicklist = self.names()
		if connection.get_nickname() != nicklist[0]:
			connection.nick(nicklist[0])
	
	def on_nicknameinuse(self, bot, connection, event):
		nicklist = self.names()
		if event.arguments[0] not in nicklist:
			return # must have been manually renicked
		
		new_nick_position = nicklist.index(event.arguments[0]) + 1
		if new_nick_position == len(nicklist):
			print('Unable to acquire any nickname')
			bot.quit(connection, event)
		
		new_nick = nicklist[new_nick_position]
		if new_nick == connection.get_nickname():
			connection.execute_delayed(self.nick_delay, self.get_ideal_nick, (bot, connection))
		else:
			connection.nick(new_nick)
	
	def on_nonicknamegiven(self, bot, connection, events):
		self.get_ideal_nick(bot, connection)
	
	def names(self):
		return bot.db.get_all('nickname|' + bot.server_name) + ['ResponseBot']
