from datetime import datetime, timedelta
from collections import defaultdict

def init():
    Tell()

class Tell():
    auth_commands = {
        'tell': 0,
    }
    command_descriptions = {
        'tell': """
            Stores a message to be sent later when someone is around
            [message] will be sent to [nick] whenever they next speak in the channel the command was issued in
            This command will not work in private messages sent to the bot
            Syntax: tell [nick] [message]
        """,
    }
    
    def __init__(self):
        event_handler.hook('modulehandler:before_init_modules', self.on_before_init_modules)
        event_handler.hook('modulehandler:after_load_modules', self.on_after_load_modules)
        
        event_handler.hook('help:get_command_description', self.get_command_description)
        
        event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
        event_handler.hook('commands:do_auth_command', self.do_auth_command)
        
        event_handler.hook('messages:on_handle_messages', self.on_handle_messages, -1)
        
        self.messages = defaultdict(lambda: defaultdict(list))
    
    def on_before_init_modules(self, module_handler, bot, event_handler, first_time):
        bot.module_parameters['tell:messages'] = self.messages
    
    def on_after_load_modules(self, module_handler, bot, event_handler, first_time):
        self.messages = bot.module_parameters.pop('tell:messages', self.messages)
    
    def get_command_description(self, bot, command):
        if command in self.command_descriptions:
            return self.command_descriptions[command]
    
    def get_auth_commands(self, bot):
        return self.auth_commands
    
    def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
        if command not in self.auth_commands:
            return False # not for us
        
        if command == 'tell':
            if reply_target[0] != '#':
                return False
            
            try:
                nick, message = parameters.strip().split(' ', 1)
            except ValueError:
                return False
            
            message = message.strip()
            for word in bot.db.get_all('tell_prefix'):
                word_len = len(word)
                if message[:word_len].lower() == word.lower():
                    message = message[word_len:].strip()
                    break
            
            self.messages[reply_target][nick.lower()].append(
                StoredMessage(nick, event.source, message.strip())
            )
            bot.send(connection, reply_target, bot.db.get_random('yes'), event)
            return True
        
        return False
    
    def on_handle_messages(self, bot, connection, event, message, is_public, is_action, reply_target, auth_level):
        if not is_public:
            return False
        
        messages = self.messages[reply_target][event.source.nick.lower()]
        
        if not messages:
            return False
        
        for stored_message in messages:
            time_delta = datetime.now() - stored_message.datetime
            
            days = time_delta.days
            if days:
                time_delta -= timedelta(days = days)
            
            hours, remainder = divmod(time_delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            time_pieces = []
            days and time_pieces.append(self.format_time_piece('day', days))
            hours and time_pieces.append(self.format_time_piece('hour', hours))
            minutes and time_pieces.append(self.format_time_piece('minute', minutes))
            seconds and time_pieces.append(self.format_time_piece('second', seconds))
            
            message = '%s: message from %s %s: %s' % (
                event.source.nick,
                stored_message.source.nick,
                (', '.join(time_pieces[:2]) + ' ago') if time_pieces else 'just now',
                stored_message.message,
            )
            
            bot.send(connection, reply_target, message, event, process_message = False)
        
        messages.clear()
        
        return False
    
    def format_time_piece(self, name, value):
        return '%d %s%s' % (value, name, '' if value == 1 else 's')

class StoredMessage():
    def __init__(self, destination, source, message):
        self.destination = destination
        self.source = source
        self.message = message
        
        self.datetime = datetime.now()
