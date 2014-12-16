import importlib
import logging
import glob
import sys
import os

from eventhandler import EventHandler

class ModuleHandler():
	def __init__(self, bot):
		self.event_handler = EventHandler()
		self.bot = bot
		self.load_modules(True)
	
	def load_modules(self, first_time = False):
		module_files = glob.glob(os.path.dirname(__file__) + '/modules/*.py')
		module_names = ['modules.' + os.path.basename(f)[:-3] for f in module_files]
		imported_modules = []
		
		if any(result is False for result in self.fire_event('modulehandler:before_load_modules', (self, self.bot, self.event_handler, first_time))):
			return False
		
		logging.info('Loading modules')
		
		# try to import all modules - if failed, return before we break our previous event handlers
		for module in module_names:
			if module in sys.modules:
				module = sys.modules[module]
				importfunc = importlib.reload
			else:
				importfunc = importlib.import_module
			
			try:
				module = importfunc(module)
				module.bot = self.bot
				module.event_handler = self.event_handler
				imported_modules.append(module)
			except BaseException as e:
				if first_time:
					raise
				# if we fail out here, old event hooks remain in place
				error = 'module "%s" unable to import: %s: %s' % (str(module), type(e).__name__, e)
				logging.exception(error)
				print(error)
				return False
		
		if any(result is False for result in self.fire_event('modulehandler:before_init_modules', (self, self.bot, self.event_handler, first_time))):
			return False
		
		# we've imported with no problems - break old hooks, and try to add new
		self.event_handler.clear_module_hooks()
		self.event_handler.importing_modules = True
		
		for module in imported_modules:
			try:
				module.init()
			except BaseException as e:
				if first_time:
					raise
				# if we fail out here, this module will NOT have hooked its events
				error = 'module "%s" unable to init: %s: %s' % (str(module), type(e).__name__, e)
				logging.exception(error)
				print(error)
		
		self.event_handler.importing_modules = False
		
		self.fire_event('modulehandler:after_load_modules', (self, self.bot, self.event_handler, first_time))
		
		return True
	
	def fire_event(self, key, parameters):
		return self.event_handler.fire(key, parameters)
	
	def hook_event(self, key, function, priority = 500):
		return self.event_handler.hook(key, function, priority, permanent)
	
	def get_event_handlers(self, key):
		return self.event_handler.get_handlers(key)
