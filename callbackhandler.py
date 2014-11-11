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

	def exists(self, key):
		return key in self.callbacks

	def run(self, key, additional_parameters = {}):
		if key in self.callbacks:
			callback = self.callbacks.pop(key)
			callback['parameters'].update(additional_parameters)
			return callback['function'](**callback['parameters'])
		
		return None
