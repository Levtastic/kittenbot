import logging

def init():
	event_handler.hook('irc:on_privmsg', on_message)
	event_handler.hook('irc:on_pubmsg', on_message)
	event_handler.hook('irc:on_action', on_message)
	event_handler.hook('commands:on_message', on_message)
	
	event_handler.hook('console:on_input', on_input)
	
	event_handler.hook('bot:on_send_message', on_send_message)

def on_input(bot, connection, event, command):
	if '\n' not in command:
		on_message(bot, connection, event, 200)
		return True
	
	return False

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
	
	source = event.source.nick
	reply_target = is_public and event.target or source
	
	if any(result is False for result in event_handler.fire('messages:on_before_handle_messages', (bot, connection, event, is_public, is_action, reply_target, auth_level))):
		return False
	
	for handler in event_handler.get_handlers('messages:on_handle_messages'):
		try:
			if handler(bot, connection, event, is_public, is_action, reply_target, auth_level) is True:
				return
		
		except BaseException as e:
			error = 'error in message handling function: %s: %s' % (type(e).__name__, e)
			logging.exception(error)
			print(error)
	
	# if we get here, no handler wanted the message, so we're done - bot does nothing

def on_send_message(bot, connection, target, message, event, process_message):
	if target == '-CONSOLE':
		return False
	
	if not process_message:
		return False
	
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
		send_func = message_type_matches[0] == '-' and connection.privmsg or connection.action
	
	send_func(target, message)
	
	return True
