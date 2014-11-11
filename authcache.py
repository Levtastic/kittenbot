class AuthCache():
	def __init__(self):
		self.authcache = {}
	
	def set(self, nickname, auth_level):
		self.authcache[nickname] = auth_level
	
	def get(self, nickname):
		if nickname in self.authcache:
			return self.authcache[nickname]
		
		return None
	
	def unset(self, nickname):
		if nickname in self.authcache:
			self.authcache.remove(nickname)
	
	def exists(self, nickname):
		return nickname in self.authcache
