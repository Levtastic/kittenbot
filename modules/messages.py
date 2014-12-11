import re

def init():
	event_handler.hook('irc:on_privmsg', on_message)
	event_handler.hook('irc:on_pubmsg', on_message)
	event_handler.hook('irc:on_action', on_message)
	event_handler.hook('commands:on_message', on_message)
	
	event_handler.hook('bot:send_message', send_message)

def on_message(bot, connection, event, auth_level = None):
	if event.type == 'privmsg':
		is_public = False
		is_action = False
	elif event.type == 'pubmsg':
		is_public = True
		is_action = False
	elif event.type == 'action':
		is_public = event.target[0] == '#'
		is_action = True
	else:
		return
	
	if any(result is False for result in event_handler.fire('messages:on_before_handle_message', (bot, connection, event, is_action, is_public, auth_level))):
		return
	
	reply_target = is_public and event.target or event.source.nick
	
	# check if it's a command
	if not is_action:
		command = None
		
		if not is_public:
			command = event.arguments[0].strip()
		else:
			message_split = event.arguments[0].split(':', 1)
			if len(message_split) == 2 and message_split[0].lower().strip() == bot.connection.get_nickname().lower():
				command = message_split[1]
		
		# if sent in private message or prefixed by our name, try it as a command
		if command:
			if any(event_handler.fire('messages:do_command', (bot, connection, event, command, reply_target, auth_level))):
				return
	
	# not a failed or successful command, so test it against our response database
	message = get_message(connection, event, is_action)
	if message:
		bot.send(connection, reply_target, message, event)
		return
	
	# still no hit? Nothing to do with us, move along.

def get_message(connection, event, is_action):
	message_type_code = is_action and '*' or '-'
	
	# Try to get a message as-is, then try swapping in aliases
	for name in [False, connection.get_nickname()] + bot.db.get_all('nick_alias'):
		if name:
			message = re.sub(re.escape(name), '!me', event.arguments[0], flags = re.IGNORECASE)
		else:
			message = event.arguments[0]
		
		message = bot.db.get_reply(message, message_type_code)
		if message:
			return message

def send_message(bot, connection, target, message, event):
	message_type_matches = []
	
	for c in message:
		if c in ('-', '*') and c not in message_type_matches:
			message_type_matches.append(c)
		else:
			break
	else:
		return False
	
	if not message_type_matches:
		return False
	
	message = message[message.index(message_type_matches[-1])+1:]
	if message[0] == ' ':
		message = message[1:]
	
	original_message_type_code = ''
	if event:
		original_message_type_code = event.type == 'action' and '*' or '-'
	
	if original_message_type_code in message_type_matches:
		send_func = original_message_type_code == '-' and connection.privmsg or connection.action
	else:
		send_func = message_type_matches[0] == '-' and connection.privms or connection.action
	
	send_func(target, message)
	
	return True
