import irc.bot

from callbackhandler import CallbackHandler
from authcache import AuthCache
from responsedatabase import ResponseDatabase

class ResponseBot(irc.bot.SingleServerIRCBot):
	known_commands = [
		'die',
	]
	
	def __init__(self, nickname, realname, server, port = 6667,
			channel_list = [], db_name = 'responsebot.db', command_aliases = {}):
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, realname)
		self.channel_list = channel_list
		self.command_aliases = command_aliases
		self.callback_handler = CallbackHandler()
		self.auth_cache = AuthCache()
		self.database = ResponseDatabase(db_name)
	
	def on_nicknameinuse(self, connection, event):
		print('Unable to acquire nickname %s' % connection.get_nickname)
		self.die()
	
	def on_welcome(self, connection, event):
		for channel in self.channel_list:
			connection.join(channel)
	
	def on_privmsg(self, connection, event):
		self.do_command(connection, event, event.arguments[0])
	
	def on_pubmsg(self, connection, event):
		a = event.arguments[0].split(':', 1)
		if len(a) > 1 and a[0].lower().strip() == self.connection.get_nickname().lower():
			self.do_command(connection, event, a[1].strip().lower())
	
	def on_whoisuser(self, connection, event):
		self.callback_handler.run(
			'whois-%s' % event.arguments[0],
			{
				'auth_level': self.database.get_whois_auth_level(event.arguments)
			}
		)
	
	def do_command(self, connection, event, command, auth_level = None):
		if command in self.command_aliases:
			command = self.command_aliases[command]
		
		if command not in self.known_commands:
			connection.action(event.target, 'ignores %(speaker)s' % self.get_string_parameters(connection, event))
			return
		
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
		
		if command == 'die' and auth_level > 80:
			print('die command issued by %s in %s' % (event.source.nick, event.target))
			for channel in self.channel_list:
				connection.action(channel, 'leaves the room')
				connection.part(channel)
			self.die('zzz')
			return
	
	def get_string_parameters(self, connection, event):
		return {
			'speaker': event.source.nick,
			'channel': event.target,
		}
