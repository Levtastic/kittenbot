from modules.resources.callbackhandler import CallbackHandler

def init():
    Undo()

class Undo():
    undo_stack = []
    redo_stack = []
    auth_commands = {
        'undo': 30,
        'redo': 30,
    }
    command_descriptions = {
        'undo': """
            Undoes the last database action (such as add or remove)
            Note: Using "undo, redo, undo" has the same final effect as simply doing "undo" once, as "undo" will also undo a "redo"
            Syntax: undo
        """,
        'redo': """
            redoes the last database action that was undone using "undo" (such as add or remove)
            Note: Using "undo, redo, undo" has the same final effect as simply doing "undo" once, as "undo" will also undo a "redo"
            Syntax: redo
        """,
    }
    
    def __init__(self):
        event_handler.hook('modulehandler:before_init_modules', self.on_before_init_modules)
        event_handler.hook('modulehandler:after_load_modules', self.on_after_load_modules)
        
        event_handler.hook('help:get_command_description', self.get_command_description)
        
        event_handler.hook('commands:get_auth_commands', self.get_auth_commands)
        event_handler.hook('commands:do_auth_command', self.do_auth_command)
        
        event_handler.hook('db_commands:on_after_add', self.on_after_add)
        event_handler.hook('db_commands:on_before_remove', self.on_before_remove)
        event_handler.hook('db_commands:on_after_remove', self.on_after_remove)
        event_handler.hook('db_commands:on_before_set', self.on_before_set)
        event_handler.hook('db_commands:on_after_set', self.on_after_set)
        
        self.callback_handler = CallbackHandler('undo')
    
    def on_before_init_modules(self, module_handler, bot, event_handler, first_time):
        # we're about to be replaced!
        bot.module_parameters['undo:undo_stack'] = self.undo_stack
        bot.module_parameters['undo:redo_stack'] = self.redo_stack
    
    def on_after_load_modules(self, module_handler, bot, event_handler, first_time):
        self.undo_stack = bot.module_parameters.pop('undo:undo_stack', [])
        self.redo_stack = bot.module_parameters.pop('undo:redo_stack', [])
    
    def get_command_description(self, bot, command):
        if command in self.command_descriptions:
            return self.command_descriptions[command]
    
    def get_auth_commands(self, bot):
        return self.auth_commands
    
    def do_auth_command(self, bot, connection, event, command, parameters, reply_target, auth_level):
        if command not in self.auth_commands:
            return False # not for us
        
        if command == 'undo':
            if not self.undo_stack:
                return False
            
            undo = self.undo_stack.pop()
            if undo:
                undo['function'](*undo['parameters'])
                
                self.add_to_stack(bot, self.redo_stack, undo['alt_function'], undo['alt_parameters'], undo['function'], undo['parameters'])
                
                bot.send(connection, reply_target, bot.db.get_random('yes'), event)
                event_handler.fire('undo:on_undo', (bot, connection, event, command, parameters, reply_target, auth_level))
                return True
        
        elif command == 'redo':
            if not self.redo_stack:
                return False
            
            redo = self.redo_stack.pop()
            if redo:
                redo['function'](*redo['parameters'])
                
                self.add_to_stack(bot, self.undo_stack, redo['alt_function'], redo['alt_parameters'], redo['function'], redo['parameters'])
                
                bot.send(connection, reply_target, bot.db.get_random('yes'), event)
                event_handler.fire('undo:on_redo', (bot, connection, event, command, parameters, reply_target, auth_level))
                return True
        
        return False
    
    def on_after_add(self, bot, connection, event, reply_target, auth_level, key, value):
        self.add_to_stack(bot, self.undo_stack, bot.db.delete, (key, value), bot.db.add, (key, value))
    
    def on_before_remove(self, bot, connection, event, reply_target, auth_level, key, value):
        db_key, old_value = bot.db.get_key_value(key, value)
        if old_value:
            self.callback_handler.add(
                'remove|%s|%s' % (key, value),
                self.stack_undo_remove,
                (bot, db_key, old_value, value)
            )
    
    def on_after_remove(self, bot, connection, event, reply_target, auth_level, key, value):
        self.callback_handler.run('remove|%s|%s' % (key, value))
    
    def on_before_set(self, bot, connection, event, reply_target, auth_level, key, values):
        old_values = bot.db.get_all(key)
        if old_values:
            self.callback_handler.add(
                'set|%s|%s' % (key, '|'.join(values)),
                self.stack_undo_set,
                (bot, key, old_values, values)
            )
    
    def on_after_set(self, bot, connection, event, reply_target, auth_level, key, values):
        self.callback_handler.run('set|%s|%s' % (key, '|'.join(values)))
    
    def stack_undo_remove(self, bot, key, old_value, new_value):
        self.add_to_stack(bot, self.undo_stack, bot.db.add, (key, old_value), bot.db.delete, (key, new_value))
    
    def stack_undo_set(self, bot, key, old_values, new_values):
        self.add_to_stack(bot, self.undo_stack, bot.db.set, (key, old_values), bot.db.set, (key, new_values))
    
    def add_to_stack(self, bot, stack, function, parameters, alt_function, alt_parameters):
        if not isinstance(parameters, (tuple, list)):
            parameters = (parameters, )
        
        stack.append({
            'function': function,
            'parameters': parameters,
            'alt_function': alt_function,
            'alt_parameters': alt_parameters,
        })
        
        stack_difference = len(stack) - int(bot.db.get('undo_stack_size', default_value = 10))
        if stack_difference > 0:
            stack = stack[stack_difference:]
