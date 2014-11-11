import sqlite3
import irc.bot

class ResponseBot(irc.bot.SingleServerIRCBot):
	def __init__(self, nickname, realname, channel_list, server, port = 6667, db_name = 'responsebot.db', command_aliases = {}):
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
		self.channel_list = channel_list
		self.command_aliases = command_aliases
		self.database = sqlite3.connect(db_name)
		cursor = self.database.cursor()
		cursor.execute("""
			SELECT
				COUNT(1)
			FROM
				sqlite_master
			WHERE
				type = 'table'
		""")
		if cursor.fetchone()[0] < 1:
			from dbbuilder import DbBuilder
			db_builder = DbBuilder()
			db_builder.build_database(self.database)
	
	def on_nicknameinuse(self, connection, event):
		error_message = 'Unable to acquire nickname %s' % connection.get_nickname
		print(error_message)
		self.die(error_message)
	
	def on_welcome(self, connection, event):
		for channel in self.channel_list:
			connection.join(channel)
	
	def on_privmsg(self, connection, event):
		if self.get_user_auth_level(connection, event, event.source.nick) >= 50:
			self.do_command(connection, event, event.arguments[0])
	
	def on_pubmsg(self, connection, event):
		a = event.arguments[0].split(':', 1)
		if len(a) > 1 and a[0].lower().strip() == self.connection.get_nickname().lower():
			self.do_command(connection, event, a[1].strip().lower())
	
	def get_user_auth_level(self, connection, event, nickname):
		connection.whois(nickname)
		return 0
	
	def on_whoisuser(self, connection, event):
		print(event.arguments)
	
	def do_command(self, connection, event, command):
		if command in self.command_aliases.keys():
			command = self.command_aliases[command]
		
		if command == 'die':
			for channel in self.channel_list:
				connection.action(channel, 'leaves the room')
				connection.part(channel)
			self.die('zzz')
		else:
			connection.action(event.target, 'ignores %(speaker)s' % self.get_string_parameters(connection, event))
	
	def get_string_parameters(self, connection, event):
		return {
			'speaker': event.source.nick,
			'channel': event.target,
		}
