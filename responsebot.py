import logging
import irc.bot

from modulehandler import ModuleHandler

class ResponseBot(irc.bot.SingleServerIRCBot):
    def __init__(self, nickname, realname, server_name, server, module_parameters = {}):
        # init bot framework
        irc.bot.SingleServerIRCBot.__init__(self, [server], nickname, realname)
        
        # set lenient encoding to avoid encoding-related crash
        irc.client.ServerConnection.buffer_class = irc.buffer.LenientDecodingLineBuffer
        
        # store passed variables for later use
        self.server_name = server_name
        self.module_parameters = module_parameters
        
        # set up helper classes for later use
        self.module_handler = ModuleHandler(self)
        
        # max messages a second, to avoid flooding out
        # note: may cause blocking which could make the bot fail to respond to a ping
        rate_limit = self.db.get('connection_rate_limit|' + server_name) or self.db.get('connection_rate_limit')
        if rate_limit:
            self.connection.set_rate_limit(float(rate_limit))
        
        # hook into IRC event handler to pass events to our event handler
        self.reactor.add_global_handler('all_events', self._irc_events)
        
        # init event
        self.module_handler.fire_event('bot:finish_init', self)
    
    def _irc_events(self, connection, event):
        self.module_handler.fire_event('irc:on_' + event.type, (self, connection, event))
    
    def start(self):
        self.module_handler.fire_event('bot:on_start', self)
        super(ResponseBot, self).start()
    
    def get_version(self):
        version_info = [info for info in self.module_handler.fire_event('bot:on_get_version', self) if info]
        version_info.append(super(ResponseBot, self).get_version())
        return ' | '.join(version_info)
    
    def send(self, connection, target, message, *args, **kwargs):
        connection.privmsg(target, message)
        return True
    
    def quit(self, connection, event, message = ''):
        for process_function in self.module_handler.get_event_handlers('bot:on_quit'):
            try:
                if process_function(self, connection, event, message) is False:
                    return False
            except BaseException as e:
                error = 'error in message processing function: %s: %s' % (type(e).__name__, e)
                logging.exception(error)
                print(error)
        
        # die later, after any final issues have been handled
        self.execute_delayed(connection, 1, self.die, (message, ))
        return True
    
    def execute_delayed(self, connection, delay, function, arguments):
        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            
            except (KeyboardInterrupt, SystemExit):
                raise
            
            except BaseException as e:
                error = 'Exception in delayed execution: %s: %s' % (type(e).__name__, e)
                logging.exception(error)
                print(error)
                
                return False
        
        return connection.execute_delayed(delay, wrapper, arguments)
