def init():
	bot.helpers = Helpers()

class Helpers():
	def list_split(self, list, split_size):
		split_list = []
		
		for line in zip(*[iter(list)] * split_size):
			split_list.append(line)
		
		left_over = len(list) % split_size
		if left_over:
			split_list.append(list[-left_over:])
		
		return split_list

	def get_auth_commands(self, bot):
		auth_commands = {}
		
		for result in event_handler.fire('commands:get_auth_commands', bot):
			if result:
				auth_commands.update(result)
		
		return auth_commands
