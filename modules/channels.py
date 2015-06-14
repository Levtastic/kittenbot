from callbackhandler import CallbackHandler

def init():
    Channels()

class Channels():
    def __init__(self):
        event_handler.hook('irc:on_invite', self.on_invite)
        event_handler.hook('irc:on_kick', self.on_kick)
        event_handler.hook('irc:on_join', self.on_join)
        event_handler.hook('irc:on_namreply', self.on_namreply)
        event_handler.hook('irc:on_channelisfull', self.on_needinvite)
        event_handler.hook('irc:on_inviteonlychan', self.on_needinvite)
        event_handler.hook('irc:on_badchannelkey', self.on_needinvite)
        
        event_handler.hook('bot:on_before_send_message', self.on_before_send_message)
        event_handler.hook('bot:on_quit', self.on_quit)
        
        self.callback_handler = CallbackHandler()
    
    def on_invite(self, bot, connection, event):
        # invites can only be sent by channel ops, so we don't need to
        # worry too much about this being abused
        channel = event.arguments[0].lower()
        bot.db.add('channel|' + bot.server_name, channel)
        connection.join(channel)
    
    def on_kick(self, bot, connection, event):
        # if we get kicked, remove the channel
        if event.arguments[0] == connection.get_nickname():
            bot.db.delete('channel|' + bot.server_name, event.target)
    
    def on_join(self, bot, connection, event):
        if event.source.nick == connection.get_nickname():
            # register a callback for when we get the namreply for this channel, and know who's in it
            # (necessary for use of !someone in greeting messages)
            self.callback_handler.add('greetchannel-%s' % event.target, self.greet_channel, (bot, event.target, connection, event))
    
    def on_namreply(self, bot, connection, event):
        channel = event.arguments[1]
        # we just got the information that populates the channel user list? now we can greet the channel
        self.callback_handler.run('greetchannel-%s' % channel)
        
        # if there's only one nick in here, it's us, so we remove the channel from autojoin
        if len(bot.channels[channel].users()) == 1:
            bot.db.delete('channel|' + bot.server_name, channel)
    
    def greet_channel(self, bot, channel, connection, event):
        bot.send(connection, channel, bot.db.get_random('join', channel = channel), event)
    
    def on_needinvite(self, bot, connection, event):
        channel = event.arguments[0]
        if channel and channel[0] == '#':
            for command in bot.db.get_all('invite_command|' + bot.server_name):
                target, message = command.split('|', 1)
                message = message % {'channel': channel}
                bot.send(connection, target, message, event, False)
    
    def on_before_send_message(self, bot, connection, target, message, event):
        if target[0] == '#' and target not in bot.channels:
            return False
        
        return True
    
    def on_quit(self, bot, connection, event, message):
        homes = bot.db.get_all('home|' + bot.server_name)
        for channel in bot.channels:
            if channel not in homes:
                # say goodbye!
                bot.send(connection, channel, bot.db.get_random('part'), event)
                connection.part(channel, message)
