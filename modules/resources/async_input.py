import time
from threading import Thread

try:
	import readline
except ImportError:
	pass

try: # py2
	_import = __import__('queue', fromlist = ['Queue'])
except ImportError: # py3
	_import = __import__('Queue', fromlist = ['Queue'])

Queue = _import.Queue

try: # py2
	input = raw_input
except NameError: # py3
	pass

class AsyncInput():
	def __init__(self, after = None, prefix = '', sentinel = None, delimiter = '\\'):
		"""
			This class is designed to run in the background of a larger application, and allow back-door console access.
			The main program should periodically call get() to get user-entered multi-line inputs one at a time.
			
			This class starts listening for user input on start().
			You MUST call start() after creating an instance if you want user input to be collected.
			
			By default the class will continually get user input until stopped.
			If you only want one input, set ready to False when calling get().
			
			@after: if not None, is printed after input successfully received.
			@prefix: output before each line of input.
			@sentinel: If not None, input waits for this string to appear before finishing the input string.
			@delimiter: If no sentinel is provided, this string can be used on the end of input lines to continue multi-line input.
		"""
		
		self.queue = Queue()
		self.running = False
		self._ready = True
		
		self.after = after
		self.prefix = prefix
		self.sentinel = sentinel
		self.delimiter = delimiter
	
	def start(self, ready = True):
		self.running = True
		self._ready = ready
		
		thread = Thread(target = self._main_loop)
		thread.daemon = True # this thread can't keep the program alive
		thread.start()
	
	def stop(self):
		self.running = False
	
	def empty(self):
		return self.queue.empty()
	
	def get(self, ready = True):
		self._ready = ready
		
		if not self.queue.empty():
			return self.queue.get(False)
		
		return None
	
	def ready(self):
		self._ready = True
	
	def _main_loop(self):
		while self.running:
			if self.queue.empty() and self._ready:
				self.queue.put(self._get_input())
				
				if self.after is not None:
					print(self.after)
			
			else:
				time.sleep(0.2)
	
	def _get_input(self):
		get_input = lambda: input(self.prefix)
		
		if self.sentinel is not None:
			return '\n'.join(iter(get_input, self.sentinel))
		
		if not self.delimiter:
			return get_input()
		
		user_input = self.delimiter
		delim_length = len(self.delimiter)
		
		while user_input[-delim_length:] == self.delimiter:
			user_input = user_input[:-delim_length] + '\n' + get_input()
		
		return user_input[1:] # clip off leading \n
