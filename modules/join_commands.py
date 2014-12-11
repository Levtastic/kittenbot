import logging

def init():
	event_handler.hook('irc:on_welcome', on_welcome)

def on_welcome(bot, connection, event):
	for command in bot.db.get_all('join_command|' + bot.server_name):
		try:
			parts = [s.strip() for s in command.split('"') if s.strip()]
			object_name = parts[0]
			if object_name == 'connection':
				object = connection
				function_name = parts[1]
				parameters = parts[2:]
			elif object_name == 'bot':
				object = bot
				function_name = parts[1]
				parameters = parts[2:]
			else:
				object = connection
				function_name = parts[0]
				parameters = parts[1:]
			
			function = getattr(object, function_name)
			function(*parameters)
		
		except BaseException as e:
			error = 'join_command "%s" unable to execute: %s %s' % (command, str(type(e)), str(e))
			print(error)
			logging.error(error)
