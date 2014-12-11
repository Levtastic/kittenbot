import logging

class EventHandler():
	importing_modules = False
	events = {}
	
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
		if key in self.events:
			self.events[key].sort(key = lambda hook: hook['priority'])
			
			for hook in self.events[key]:
				try:
					if isinstance(parameters, dict):
						results.append(hook['function'](**parameters))
					elif isinstance(parameters, (list, tuple)):
						results.append(hook['function'](*parameters))
					else:
						results.append(hook['function'](parameters))
				
				except BaseException as e:
					error = 'event "%s" hit an exception in a handler: %s %s' % (key, type(e), e)
					logging.exception(error)
					print(error)
		
		return results
	
	def clear_module_hooks(self):
		for key, event in self.events.items():
			self.events[key] = [hook for hook in event if not hook['from_module']]
