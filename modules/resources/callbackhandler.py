import time
    
class CallbackHandler:
    _callbacks = {}
    
    def __init__(self, unique_prefix = ''):
        self.unique_prefix = unique_prefix + '|'
    
    def __getattr__(self, name):
        self.expire()
        return getattr(self, '_' + name)
    
    def _prefix_key(self, key):
        return self.unique_prefix + key
    
    def _add(self, key, function, parameters = {}, ttl = 60.0):
        self._callbacks[self._prefix_key(key)] = Callback(function, parameters, ttl)
        return True
    
    def _get(self, key):
        key = self._prefix_key(key)
        if key in self._callbacks:
            return self._callbacks.pop(key)
        
        return None
    
    def _remove(self, key):
        key = self._prefix_key(key)
        if key in self._callbacks:
            self._callbacks.remove(key)
            return True
        
        return False
    
    def _update_parameters(self, key, parameters):
        key = self._prefix_key(key)
        if key in self._callbacks:
            return self._callbacks[key].update_parameters(parameters)
        
        return False
    
    def _exists(self, key):
        return self._prefix_key(key) in self._callbacks
    
    def _run(self, key, parameters = None):
        key = self._prefix_key(key)
        if key in self._callbacks:
            return self._callbacks.pop(key).run(parameters)
        
        return None
    
    def _extend(self, key, ttl):
        key = self._prefix_key(key)
        if key in self._callbacks:
            self._callbacks[key].ttl += ttl
            return True
        
        return False
    
    def expire(self):
        self._callbacks = {key: callback for key, callback in self._callbacks.items() if not callback.should_expire()}

class Callback:
    def __init__(self, function, parameters = {}, ttl = 60.0):
        self.function = function
        self.parameters = parameters
        self.ttl = ttl
        self.created_at = time.time()
    
    def update_parameters(self, parameters):
        if parameters:
            if isinstance(self.parameters, dict):
                self.parameters.update(parameters)
            elif isinstance(parameters, (list, tuple)):
                self.parameters += parameters
            else:
                self.parameters.append(parameters)
            
            return True
        
        return False
    
    def run(self, parameters = None):
        self.update_parameters(parameters)
        
        if isinstance(self.parameters, dict):
            return self.function(**self.parameters)
        elif isinstance(self.parameters, (list, tuple)):
            return self.function(*self.parameters)
        else:
            return self.function(self.parameters)
    
    def should_expire(self):
        return self.created_at + self.ttl < time.time()
