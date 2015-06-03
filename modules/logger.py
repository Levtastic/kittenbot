import logging

def init():
    event_handler.hook('bot:finish_init', on_init_finished, 0)
    event_handler.hook('bot:on_start', on_bot_start, 0)
    event_handler.hook('irc:on_welcome', on_welcome, 0)
    event_handler.hook('irc:on_privnotice', on_privnotice, 0)
    event_handler.hook('irc:on_invite', on_invite, 0)
    event_handler.hook('irc:on_join', on_join, 0)
    event_handler.hook('irc:on_part', on_part, 0)
    event_handler.hook('irc:on_kick', on_kick, 0)
    event_handler.hook('irc:on_nick', on_nick, 0)
    event_handler.hook('irc:on_nicknameinuse', on_nicknameunavailable, 0)
    event_handler.hook('irc:on_nickcollision', on_nicknameunavailable, 0)
    event_handler.hook('irc:on_unavailresource', on_nicknameunavailable, 0)
    event_handler.hook('irc:on_channelisfull', on_cant_join, 0)
    event_handler.hook('irc:on_inviteonlychan', on_cant_join, 0)
    event_handler.hook('irc:on_badchannelkey', on_cant_join, 0)
    event_handler.hook('irc:on_bannedfromchan', on_cant_join, 0)
    
    # last, so only fires if no other handler stops the shutdown
    event_handler.hook('bot:on_quit', on_quit, 1000)

def on_init_finished(bot):
    logging.info('Initialised')

def on_bot_start(bot):
    logging.info('Connecting to %s:%d as %s' % (bot.server_list[0].host, bot.server_list[0].port, bot._nickname))

def on_welcome(bot, connection, event):
    logging.info('Connected')

def on_privnotice(bot, connection, event):
    logging.info('Private notice from %s: "%s"' % (event.source, event.arguments[0]))

def on_invite(bot, connection, event):
    logging.info('Invited to %s by %s' % (event.arguments[0], event.source.nick))

def on_join(bot, connection, event):
    if event.source.nick == connection.get_nickname():
        logging.info('Joined %s' % event.target)

def on_part(bot, connection, event):
    if event.source.nick == connection.get_nickname():
        logging.info('Leaving %s' % event.target)

def on_kick(bot, connection, event):
    if event.arguments[0] == connection.get_nickname():
        logging.info('Kicked from %s by %s: %s' % (event.target, event.source.nick, event.arguments[1]))

def on_nick(bot, connection, event):
    if event.target == connection.get_nickname():
        logging.info('Renicked to ' + connection.get_nickname())

def on_nicknameunavailable(bot, connection, event):
    logging.info('Unable to renick to %s. Rejection type: %s' % (event.arguments[0], event.type))

def on_cant_join(bot, connection, event):
    logging.info('Unable to join %s. Rejection type: %s' % (event.arguments[0], event.type))

def on_quit(bot, connection, event, message):
    logging.info('Bot shutting down')
