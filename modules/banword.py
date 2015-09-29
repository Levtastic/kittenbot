import re
from collections import defaultdict

def init():
    BanWord()

class BanWord():
    auth_commands = {
        'channelbanword': 50,
        'banword': 0,
        'channelunbanword': 50,
        'unbanword': 0,
    }
    command_descriptions = {
        'channelbanword': """
            Sets a new (case insensitive) banned word for the given channel
            Banned words cause the speaker to be immediately kicked with a variable length ban
            [minutes] defaults to 5 if omitted
            Syntax: banword [channel] [minutes] [word]
        """,
        'banword': """
            Sets a new (case insensitive) banned word
            Banned words cause the speaker to be immediately kicked with a variable length ban
            [minutes] defaults to 5 if omitted
            Only works for channel operators
            Syntax: banword [minutes] [word]
        """,
        'channelunbanword': """
            Removes a (case insensitive) banned word for the given channel
            Banned words cause the speaker to be immediately kicked with a variable length ban
            Only works for channel operators
            Syntax: unbanword [channel] [word]
        """,
        'unbanword': """
            Removes a (case insensitive) banned word
            Banned words cause the speaker to be immediately kicked with a variable length ban
            Only works for channel operators
            Syntax: unbanword [word]
        """,
    }
    
    def __init__(self):
        event_handler.hook('modulehandler:before_init_modules', self.on_before_init_modules)
        event_handler.hook('modulehandler:after_load_modules', self.on_after_load_modules)
        
        event_handler.hook('help:get_command_description', self.get_command_description)
        event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
        event_handler.hook('commands:do_auth_command', self.do_auth_command)
        
        event_handler.hook('messages:on_handle_messages', self.on_handle_messages)
        
        self.banned_words = defaultdict(dict)
        self.banned_patterns = {}
    
    def on_before_init_modules(self, module_handler, bot, event_handler, first_time):
        bot.module_parameters['banword:banned_words'] = self.banned_words
    
    def on_after_load_modules(self, module_handler, bot, event_handler, first_time):
        self.banned_words = bot.module_parameters.pop('banword:banned_words', self.banned_words)
    
    def get_command_description(self, bot, command):
        if command in self.command_descriptions:
            return self.command_descriptions[command]
    
    def get_auth_commands(self, bot):
        return self.auth_commands
    
    def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
        if command not in self.auth_commands:
            return False # not for us
        
        parameters = parameters.strip()
        
        if command in ('banword', 'unbanword'):
            if reply_target[0] != '#':
                return False # not allowed in private
            
            if not parameters:
                words = list(self.banned_words[reply_target])
                if not words:
                    return False
                
                for i in range(0, len(words), 10):
                    bot.send(
                        connection,
                        reply_target,
                        ', '.join(words[i:i+10]),
                        event,
                        False
                    )
                
                return True
            
            # if the person speaking isn't op in this channel, drop out
            if not bot.channels[reply_target].is_oper(event.source.nick):
                return False
        
        if command == 'banword':
            split = parameters.split(' ', 1)
            
            try:
                minutes, word = float(split[0]), split[1]
            except (ValueError, IndexError):
                minutes, word = 5.0, parameters
            
            self.banned_words[reply_target][word.lower()] = minutes
            self.banned_patterns.pop(reply_target, None)
            
            bot.send(connection, reply_target, bot.db.get_random('yes'), event)
            return True
        
        elif command == 'unbanword':
            try:
                del self.banned_words[reply_target][parameters.lower()]
            except KeyError:
                return False
            
            if len(self.banned_words[reply_target]) == 0:
                del self.banned_words[reply_target]
            
            self.banned_patterns.pop(reply_target, None)
            
            bot.send(connection, reply_target, bot.db.get_random('yes'), event)
            return True
        
        elif command == 'channelbanword':
            split = parameters.split(' ', 2)
            if len(split) == 1:
                words = list(self.banned_words[parameters])
                if not words:
                    return False
                
                for i in range(0, len(words), 10):
                    bot.send(
                        connection,
                        reply_target,
                        ', '.join(words[i:i+10]),
                        event,
                        False
                    )
                
                return True
            
            try:
                channel, minutes, word = split[0], float(split[1]), split[2]
            except (ValueError, IndexError):
                split = parameters.split(' ', 1)
                channel, minutes, word = split[0], 5.0, split[1]
            
            self.banned_words[channel][word.lower()] = minutes
            self.banned_patterns.pop(channel, None)
            
            bot.send(connection, reply_target, bot.db.get_random('yes'), event)
            return True
        
        elif command == 'channelunbanword':
            try:
                channel, word = parameters.split(' ', 1)
            except ValueError:
                words = list(self.banned_words[parameters])
                if not words:
                    return False
                
                for i in range(0, len(words), 10):
                    bot.send(
                        connection,
                        reply_target,
                        ', '.join(words[i:i+10]),
                        event,
                        False
                    )
                
                return True
            
            try:
                del self.banned_words[channel][word.lower()]
            except KeyError:
                return False
            
            if len(self.banned_words[channel]) == 0:
                del self.banned_words[channel]
            
            self.banned_patterns.pop(channel, None)
            
            bot.send(connection, reply_target, bot.db.get_random('yes'), event)
            return True
        
        return False
    
    def on_handle_messages(self, bot, connection, event, message, is_public, is_action, reply_target, auth_level):
        # if no banned words in this channel, drop out
        if reply_target not in self.banned_words:
            return False
        
        # if we're not op in this channel, drop out
        if not bot.channels[reply_target].is_oper(connection.get_nickname()):
            return False
        
        # if the person speaking *is* op in this channel, drop out
        if bot.channels[reply_target].is_oper(event.source.nick):
            pass #return False
        
        if not self.banned_words[reply_target]:
            return False
        
        # make the pattern if it doesn't exist
        if not reply_target in self.banned_patterns:
            self.banned_patterns[reply_target] = re.compile(
                r'.*\b(%s)\b.*' % '|'.join(re.escape(word) for word in self.banned_words[reply_target].keys()),
                re.IGNORECASE
            )
        
        # see if we match any banned words
        match = self.banned_patterns[reply_target].match(message)
        if match:
            word = match.group(1)
            
            bot.send(connection, reply_target, bot.db.get_random('kick'), event)
            
            # if there are minutes, set ban
            minutes = float(self.banned_words[reply_target][word.lower()])
            if minutes > 0:
                connection.mode(reply_target, '+b *!%s' % event.source.userhost)
                
                # set unban in future
                bot.execute_delayed(
                    connection,
                    minutes * 60,
                    lambda: connection.mode(reply_target, '-b *!%s' % event.source.userhost)
                )
                
                reply_prefix = '%g minute ban' % minutes
            
            else:
                reply_prefix = 'Kicked'
            
            connection.kick(reply_target, event.source.nick, '%s for saying "%s"' % (reply_prefix, word))
            
            return True
        
        return False
