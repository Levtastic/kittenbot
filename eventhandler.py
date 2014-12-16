import inspect
import logging

class EventHandler():
	def __init__(self):
		self.importing_modules = False
		self.events = {}
	
	def hook(self, key, function, priority = 500):
		if not key in self.events:
			self.events[key] = []
		
		event = self.events[key]
		
		hook = {
			'function': function,
			'priority': priority,
			'from_module': self.importing_modules,
		}
		
		if hook in event:
			raise Exception('Event %s already hooked' % key)
		else:
			event.append(hook)
	
	def fire(self, key, parameters):
		results = []
		for handler in self.get_handlers(key):
			try:
				if isinstance(parameters, dict):
					result = handler(**parameters)
				else:
					# parameter generators return the parameters, then Nones when parameters runs out
					param_gen = self._parameter_generator(parameters)
					
					# get the number of required arguments for the handler
					handler_parameter_count = len(inspect.getfullargspec(handler)[0])
					
					if hasattr(handler, '__self__'):
						# handler is from a class, so first parameter will be the class instance
						handler_parameter_count -= 1
					
					# create parameter list of correct length for the handler
					parameters = [next(param_gen) for i in range(handler_parameter_count)]
					
					# finally, run the handler with our fancily constructed parameter list
					result = handler(*parameters)
			
			except BaseException as e:
				error = 'event "%s" hit an exception in a handler: %s: %s' % (key, type(e).__name__, e)
				logging.exception(error)
				print(error)
			else:
				if isinstance(result, StopHookIteration):
					results.append(result.get())
					return results
				else:
					results.append(result)
		
		return results
	
	def get_handlers(self, key):
		if key not in self.events:
			return []
		
		self.events[key].sort(key = lambda hook: hook['priority'])
		return [hook['function'] for hook in self.events[key]]
	
	def _parameter_generator(self, parameters):
		while True:
			if isinstance(parameters, (list, tuple)):
				if parameters:
					yield parameters[0]
					parameters = parameters[1:]
				else:
					yield None
			else:
				yield parameters
	
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
