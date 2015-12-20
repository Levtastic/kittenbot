import inspect
import logging

class EventHandler():
    def __init__(self):
        self.importing_modules = False
        self.events = {}
    
    def hook(self, key, function, priority = 500):
        if not key in self.events:
            self.events[key] = []

        def wrapper(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            
            except (KeyboardInterrupt, SystemExit):
                raise
            
            except BaseException as e:
                error = 'Event "%s" hit an exception in a handler: %s: %s' % (key, type(e).__name__, e)
                logging.exception(error)
                print(error)

            return None
        
        hook = {
            'function': wrapper,
            'naked_functon': function,
            'priority': priority,
            'from_module': self.importing_modules,
        }
        
        event = self.events[key]
        
        if hook in event:
            raise Exception('Event %s already hooked' % key)
        else:
            event.append(hook)
    
    def fire(self, key, parameters):
        results = []
        
        parameters = isinstance(parameters, (dict, list, tuple)) and parameters or (parameters, )
        
        for handler in self.get_handlers(key, True):
            function, naked_function = handler

            s = inspect.getfullargspec(naked_function)
            handler_parameters = s.args
            defaults_count = s.defaults and len(s.defaults) or 0
            
            if isinstance(parameters, dict):
                # remove unnecessary parameters (make copy of keys list to avoid resizing iteration errors)
                [parameters.pop(key) for key in list(parameters.keys()) if key not in handler_parameters]
                
                # python only allows default parameters to be at the end of the function definition,
                # so we can count backwards through the parameter list based on the number of defaults
                # to get the parameters we don't have to worry about filling
                parameters_with_defaults = handler_parameters[-defaults_count:]
                
                # add missing parameters for each handler parameter not already set and which doesn't have a default
                for key in [key for key in handler_parameters if key not in parameters.keys() and key not in parameters_with_defaults]:
                    parameters[key] = None
                
                # run the handler with our correct-size parameter dictionary
                result = function(**parameters)
            
            else:
                # get the number of required arguments for the handler
                handler_parameter_count = len(handler_parameters)
                
                if hasattr(naked_function, '__self__'):
                    # handler is from a class, so first parameter will be the class instance
                    handler_parameter_count -= 1
                
                # if we have defaults, don't require values for them
                required_parameter_count = handler_parameter_count - defaults_count
                
                # get provided number of parameters
                current_parameter_count = len(parameters)
                
                # list too short
                if current_parameter_count < required_parameter_count:
                    difference = required_parameter_count - current_parameter_count
                    
                    # make one of the same object type full of Nones of the padding length, and add it on
                    parameters += type(parameters)([None] * (difference))
                
                # list too long
                elif current_parameter_count > handler_parameter_count:
                    # or cut length down to correct length
                    parameters = parameters[:handler_parameter_count]
                
                # finally, run the handler with our correct-length parameter list
                result = function(*parameters)
                
            if isinstance(result, self.StopHookIteration):
                results.append(result.get())
                return results
            else:
                results.append(result)
        
        return results
    
    def get_handlers(self, key, include_nakeds = False):
        if key not in self.events:
            return []
        
        self.events[key].sort(key = lambda hook: hook['priority'])

        if include_nakeds:
            return [(hook['function'], hook['naked_functon']) for hook in self.events[key]]
        else:
            return [hook['function'] for hook in self.events[key]]
    
    def clear_module_hooks(self):
        for key, event in self.events.items():
            self.events[key] = [hook for hook in event if not hook['from_module']]
    
    # create one of these to halt an event when you send your return value
    # event handler will pass the internal result value back to the firing source
    # NOTE: will not work if source is directly using get_handlers
    class StopHookIteration():
        def __init__(self, result):
            self._result = result
        
        def get():
            return self._result
