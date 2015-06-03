class CallbackHandler():
    def __init__(self):
        self.callbacks = {}
    
    def add(self, key, function, parameters = {}):
        self.callbacks[key] = {
            'function': function,
            'parameters': parameters,
        }
    
    def get(self, key):
        if key in self.callbacks:
            return self.callbacks.pop(key)
        
        return None
    
    def remove(self, key):
        if key in self.callbacks:
            self.callbacks.remove(key)
            return True
        
        return False
    
    def update_parameters(self, key, parameters):
        if parameters and key in self.callbacks:
            if isinstance(self.callbacks[key]['parameters'], dict):
                self.callbacks[key]['parameters'].update(parameters)
            elif isinstance(parameters, (list, tuple)):
                self.callbacks[key]['parameters'] += parameters
            else:
                self.callbacks[key]['parameters'].append(parameters)
            
            return True
        
        return False
    
    def exists(self, key):
        return key in self.callbacks
    
    def run(self, key, parameters = None):
        self.update_parameters(key, parameters)
        
        if key in self.callbacks:
            callback = self.callbacks.pop(key)
            
            if isinstance(callback['parameters'], dict):
                return callback['function'](**callback['parameters'])
            elif isinstance(callback['parameters'], (list, tuple)):
                return callback['function'](*callback['parameters'])
            else:
                return callback['function'](callback['parameters'])
        
        return None
