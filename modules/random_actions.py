import random

def init():
    RandomActions()

class RandomActions():
    def __init__(self):
        self.run = True
        self.talked_last = []
        
        event_handler.hook('modulehandler:before_init_modules', self.on_before_init_modules)
        event_handler.hook('modulehandler:after_load_modules', self.on_after_load_modules)
        
        event_handler.hook('irc:on_part', self.on_leave)
        event_handler.hook('irc:on_kick', self.on_leave)
        event_handler.hook('irc:on_quit', self.on_leave)
        event_handler.hook('messages:on_handle_messages', self.on_message, 0)
        event_handler.hook('send:on_after_send_message', self.on_after_send_message)
    
    def on_before_init_modules(self, module_handler, bot, event_handler, first_time):
        # we're about to be replaced!
        bot.module_parameters['random_actions:talked_last'] = self.talked_last
        self.run = False 
    
    def on_after_load_modules(self, module_handler, bot, event_handler, first_time):
        self.talked_last = bot.module_parameters.pop('random_actions:talked_last', [])
        self.random_messages_loop(bot) # we run now, because we know bot.db will exist
    
    def random_messages_loop(self, bot):
        if not self.run:
            return
        
        repeat_timer = 1
        part_timing = int(bot.db.get('part_timing', default_value = 0))
        join_timing = int(bot.db.get('join_timing', default_value = 0))
        message_timing = int(bot.db.get('message_timing', default_value = 0))
        
        if bot.connection.is_connected() and (part_timing or join_timing or message_timing):
            db_channels = bot.db.get_all('channel|' + bot.server_name)
            
            for channel in bot.channels:
                # only message / part if we weren't the last person to talk in this channel
                if not channel in self.talked_last:
                    if part_timing and random.randint(1, int(part_timing)) == 1 and channel in db_channels:
                        bot.send(bot.connection, channel, bot.db.get_random('part', channel = channel))
                        bot.connection.part(channel)
                    
                    elif message_timing and random.randint(1, int(message_timing)) == 1:
                        bot.send(bot.connection, channel, bot.db.get_random('random', channel = channel))
            
            # every channel we know about, but aren't in
            for channel in [channel for channel in db_channels if channel not in bot.channels]:
                if join_timing and random.randint(1, int(join_timing)) == 1:
                    bot.connection.join(channel)
        
        else:
            repeat_timer = 60 # try again later
        
        bot.execute_delayed(bot.connection, repeat_timer, self.random_messages_loop, (bot, ))
    
    def on_leave(self, bot, connection, event):
        if event.source.nick == connection.get_nickname() and event.target in self.talked_last:
            self.talked_last.remove(event.target)
    
    def on_message(self, bot, connection, event, message, is_public, is_action, reply_target, auth_level):
        # we just got a message! We're no longer the last person to talk here
        if event.target in self.talked_last:
            self.talked_last.remove(event.target)
        
        return False
    
    def on_after_send_message(self, bot, connection, target, message, event, sent_by_module):
        # we just talked in this channel - we don't want to be the next to talk (responsebots are shy) so we record this for later
        if target[0] == '#' and target not in self.talked_last:
            self.talked_last.append(target)
