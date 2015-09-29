import logging
import re

def init():
    DbCommands()

# TODO: db aliases can be added with a new keyboard code - for example, *flees = @runs
# if a db query returns an @alias, make a second request to get the original item
# (recurse - aliases may shift over time and the second request may not result in the final destination)
# don't follow if query specifically asks for @, to allow seeing and deleting
class DbCommands():
    permitted_keys = ['join', 'no', 'part', 'random', 'yes', 'kick']
    
    auth_commands = {
        'add': 0, # unless adding non-messages, in which case 70
        'list': 0,
        'remove': 0, # unless removing non-messages, in which case 70
        'keys': 0,
        'set': 70,
        'sql': 90,
    }
    command_descriptions = {
        'add': """
            Adds a new key / value pair to the database
            For triggers, use any of the following characters, and for messages, use the second two:
            ~ for "anywhere in a sentence", - for "in a text message", and * for "in an action message"
            For example, "~-test = *successfully tests!" would respond with the action "successfully tests" any time someone said the word "test" anywhere in a written message, but not in an action
            Additionally, there are several dynamic codes that can be used in responses. For a list of these, or what they do, use "help codes"
            Syntax: add [~-*key] = [-*value]
        """,
        'list': """
            Lists matching entries in the database. Can be used to find existing responses.
            Syntax: list [key]
            Syntax: list [key] = [value]
        """,
        'remove': """
            Removes a key/value pair from the database.
            Can be used with only partially matching terms, but only succeeds if it only finds one match for them.
            Syntax: remove [partial key]
            Syntax: remove [partial key] = [partial value]
        """,
        'keys': """
            Lists all the non-trigger keys in the database you have access to.
            Syntax: keys
        """,
        'set': """
            Sets a database key to a value or list of values.
            Note: This will overwrite any previous values the key may have held
            Syntax: set key = value1 [, value2 [, value3 [ , ... ] ] ]
        """,
        'sql': """
            Runs arbitrary SQL code on the database. Obviously, be careful with this.
            Syntax: sql -force [SQL statement]
        """,
    }
    
    def __init__(self):
        event_handler.hook('help:get_command_description', self.get_command_description)
        
        event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
        event_handler.hook('commands:do_auth_command', self.do_auth_command)
    
    def get_command_description(self, bot, command):
        if command in self.command_descriptions:
            return self.command_descriptions[command]
    
    def get_auth_commands(self, bot):
        return self.auth_commands
    
    def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
        if command not in self.auth_commands:
            return False # not for us
        
        if command == 'add': # ResponseBot: *pokes ResponseBot = *bites !speaker
            try:
                key, value = [s.strip() for s in parameters.strip().split('=', 1)]
            except ValueError:
                return False
            
            key = self.process_input(connection, key, True, auth_level, False)
            value = self.process_input(connection, value, False, auth_level, False)
            
            if key not in self.permitted_keys and (key is False or value is False):
                return False
            
            # don't allow adding a user with auth higher than or equal to your own
            if 'user|%s|' % bot.server_name in key:
                if not value.isdigit():
                    return False
                
                if not int(value) < auth_level:
                    return False
            
            if any(result is False for result in event_handler.fire('db_commands:on_before_add', (bot, connection, event, reply_target, auth_level, key, value))):
                return False
            
            if bot.db.add(key, value):
                bot.send(connection, reply_target, bot.db.get_random('yes'), event)
                event_handler.fire('db_commands:on_after_add', (bot, connection, event, reply_target, auth_level, key, value))
                return True
        
        elif command == 'remove': # ResponseBot: remove *pokes ResponseBot = *bites%
            try:
                key, value = [s.strip() for s in parameters.strip().split('=', 1)]
            except ValueError:
                key = parameters
                value = ''
            
            key = self.process_input(connection, key, True, auth_level, True)
            value = self.process_input(connection, value, False, auth_level, True)
            
            if key not in self.permitted_keys and (key is False or value is False):
                return False
            
            if any(result is False for result in event_handler.fire('db_commands:on_before_remove', (bot, connection, event, reply_target, auth_level, key, value))):
                return False
            
            if bot.db.delete(key, value):
                bot.send(connection, reply_target, bot.db.get_random('yes'), event)
                event_handler.fire('db_commands:on_after_remove', (bot, connection, event, reply_target, auth_level, key, value))
                return True
        
        elif command == 'list': # ResponseBot: list 2 *pokes = *bites
            results_per_page = 5
            page = 1
            
            param_split = parameters.strip().split(' ', 1)
            if param_split[0].isdigit():
                page = int(parameters[0])
                parameters = param_split[1]
            
            try:
                key, value = [s.strip() for s in parameters.strip().split('=', 1)]
            except ValueError:
                key = parameters.strip()
                value = ''
            
            key = self.process_input(connection, key, True, auth_level, True)
            value = self.process_input(connection, value, False, auth_level, True)
            
            if key is False or value is False:
                return False
            
            results = bot.db.list(results_per_page, page, value, key, auth_level < 70)
            
            if results:
                bot.send(connection, reply_target, 'Results page %d:' % page, event, False)
                
                for result in results:
                    bot.send(connection, reply_target, ' = '.join(str(r) for r in result), event, False)
                    
                return True
        
        elif command == 'keys':
            if auth_level < 70:
                results = self.permitted_keys
            else:
                results = bot.db.list_keys(auth_level < 70)
            
            if results:
                for i in range(0, len(results), 6):
                    bot.send(
                        connection,
                        reply_target,
                        ', '.join(str(key) for key in results[i:i+6]),
                        event,
                        False
                    )
                
                return True
        
        elif command == 'set': # ResponseBot: set nickname = Name1, Name2, Name3, Name4
            try:
                key, value = [s.strip() for s in parameters.strip().split('=', 1)]
            except ValueError:
                return False
            
            values = [s.strip() for s in value.split(',') if s.strip()]
            if not values:
                return False
            
            # don't allow adding a user with auth higher than or equal to your own
            if 'user|%s|' % bot.server_name in key:
                if not all(value.isdigit() for value in values):
                    return False
                
                if not all(int(value) < auth_level for value in values):
                    return False
            
            if any(result is False for result in event_handler.fire('db_commands:on_before_set', (bot, connection, event, reply_target, auth_level, key, values))):
                return False
            
            if bot.db.set(key, values):
                bot.send(connection, reply_target, bot.db.get_random('yes'), event)
                event_handler.fire('db_commands:on_after_set', (bot, connection, event, reply_target, auth_level, key, values))
                return True
        
        elif command == 'sql': # ResponseBot: sql force SELECT * FROM vars WHERE key LIKE '%fish%'
            try:
                force, command = [s.strip() for s in parameters.strip().split(' ', 1)]
            except ValueError:
                return False
            else:
                force = force.replace('-', '').replace('/', '').replace('\\', '')
                if force in ('force', 'f') and bot.db.sql(connection, reply_target, command):
                    bot.send(connection, reply_target, bot.db.get_random('yes'), event)
                    return True
        
        return False
    
    def process_input(self, connection, message, is_key, auth_level, wildcard):
        if not message:
            return message
        
        if wildcard:
            message = message and '%' + message + '%'
        
        else: # adding or something like that, so require the ~-* starting codes
            ordered_message = self.order_message_type_codes(message, is_key)
            if not ordered_message and auth_level < 70:
                if not is_key or message not in self.permitted_keys:
                    return False
            
            message = ordered_message or message
            
            if ordered_message:
                names = [connection.get_nickname()] + bot.db.get_all('nick_alias')
                names.sort(key = len, reverse = True)
                for name in names:
                    message = re.sub(re.escape(name), '!me', message, flags = re.IGNORECASE)
        
        return message

    def order_message_type_codes(self, message, is_key):
        allowed_codes = is_key and ('~', '-', '*') or ('-', '*')
        message_type_matches = []
        
        for c in message:
            if c in allowed_codes and c not in message_type_matches:
                message_type_matches.append(c)
            else:
                break
        else:
            return False
        
        if not message_type_matches:
            return False
        
        message = message[message.index(message_type_matches[-1])+1:]
        
        if message_type_matches == ['~']:
            message_type_matches += ['-', '*']
        
        # make sure the message codes are in the right order
        codes = ''
        for code in [code for code in allowed_codes if code in message_type_matches]:
            codes += code
        
        if not codes:
            return False
        
        return codes + message
